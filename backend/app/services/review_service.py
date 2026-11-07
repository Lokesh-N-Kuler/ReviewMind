import logging
import re
from typing import List, Dict, Any, Optional
from sqlalchemy.orm import Session
from app.models.review import Review, ReviewFinding
from app.models.project import Project
from app.utils.ast_parser import analyze_code_statically
from app.services.ai_service import ai_service
from app.services.memory_service import memory_service
from app.schemas.review import ReviewResponse, FindingSchema, RecalledMemoryItem

logger = logging.getLogger(__name__)

class ReviewService:
    def _extract_code_keywords(self, code: str, language: str) -> List[str]:
        """Extract semantically meaningful keywords from code to target relevant memories."""
        keywords = set()
        code_lower = code.lower()

        # Security, architectural, and operational keywords
        sensitive_terms = [
            "sql", "select", "insert", "update", "delete", "where", "cursor", "execute",
            "eval", "exec", "subprocess", "shell", "os.system", "popen",
            "jwt", "token", "auth", "password", "secret", "bearer", "session",
            "csrf", "xss", "sanitize", "escape", "validate", "cors",
            "http", "fetch", "axios", "requests", "timeout",
            "try", "catch", "except", "error", "exception",
            "concurrency", "lock", "thread", "async", "await", "cache"
        ]
        for term in sensitive_terms:
            if term in code_lower:
                keywords.add(term)

        # Extract function and class names
        funcs = re.findall(r"(?:def|function|class)\s+([a-zA-Z0-9_]+)", code)
        for f in funcs[:5]:
            keywords.add(f.lower())

        return list(keywords)

    def perform_review(
        self,
        db: Session,
        project_id: int,
        user_id: int,
        source_code: str,
        language: str,
        title: str = "Code Review",
        file_path: str = "main",
    ) -> Review:
        """
        Complete Review Orchestrator executing the 10-step workflow:
        1. Fetch project and coding standards
        2. Perform local static code analysis (AST)
        3. Recall relevant previous project memories from Hindsight
        4. Send code, static findings, and memories to Groq
        5. Merge and deduplicate findings
        6. Calculate metrics and final score
        7. Store review in database
        8. Store findings in database
        9. Auto-retain validated findings in Hindsight
        10. Return review record
        """
        # 1. Fetch project and coding standards
        project = db.query(Project).filter(Project.id == project_id).first()
        coding_standards = project.coding_standards if project else None

        # 2. Perform static analysis locally
        static_findings = analyze_code_statically(source_code, language)

        # 3. Retrieve relevant project knowledge from Hindsight Cloud (Recall step)
        code_keywords = self._extract_code_keywords(source_code, language)
        recall_query_parts = [language, title]
        if file_path and file_path != "main":
            recall_query_parts.append(file_path)
        if code_keywords:
            recall_query_parts.append(" ".join(code_keywords[:6]))
        if static_findings:
            finding_titles = " ".join([f.get("title", "") for f in static_findings[:3]])
            recall_query_parts.append(finding_titles)
        if coding_standards:
            recall_query_parts.append(coding_standards[:80])

        recall_query = " ".join(recall_query_parts)
        logger.info(f"Targeting Hindsight recall for project {project_id} with query: '{recall_query}'")

        memory_status = "active"
        recalled_raw: List[RecalledMemoryItem] = []
        try:
            recalled_raw = memory_service.recall_memories(
                project_id=project_id,
                query=recall_query,
                limit=5
            )
            logger.info(f"Recalled {len(recalled_raw)} memories from Hindsight for project {project_id}")
        except Exception as e:
            logger.warning(f"Hindsight recall skipped for project {project_id}: {e}")
            memory_status = "unavailable"
            recalled_raw = []

        recalled_dicts = [
            {"id": m.id, "text": m.text, "tags": m.tags or []}
            for m in recalled_raw
        ]

        # 4. Send code, analysis findings, and relevant memory to Groq
        ai_output = ai_service.generate_review(
            code=source_code,
            language=language,
            file_path=file_path,
            static_findings=static_findings,
            recalled_memories=recalled_dicts,
            coding_standards=coding_standards
        )

        # 5. Merge and deduplicate findings
        all_findings: List[FindingSchema] = []
        seen_titles = set()

        # Prioritize AI findings that incorporate static insights and memory context
        for f in ai_output.findings:
            title_key = f.title.lower().strip()
            if title_key not in seen_titles:
                seen_titles.add(title_key)
                all_findings.append(f)

        # Ensure any static findings not mentioned by AI are still captured
        counter = len(all_findings) + 1
        for sf in static_findings:
            title_key = sf.get("title", "").lower().strip()
            if title_key not in seen_titles:
                seen_titles.add(title_key)
                all_findings.append(
                    FindingSchema(
                        finding_id=f"FIND-{counter:03d}",
                        title=sf.get("title", "Static Analysis Issue"),
                        category=sf.get("category", "code_quality"),
                        severity=sf.get("severity", "medium"),
                        file_path=file_path,
                        line_start=sf.get("line_start"),
                        line_end=sf.get("line_end"),
                        explanation=sf.get("explanation", ""),
                        why_it_matters=sf.get("why_it_matters", ""),
                        suggested_fix=sf.get("suggested_fix", ""),
                        corrected_code=None,
                        confidence=sf.get("confidence", 0.9),
                        memory_references=[]
                    )
                )
                counter += 1

        # 6. Calculate metrics
        metrics = {
            "critical": sum(1 for f in all_findings if f.severity == "critical"),
            "high": sum(1 for f in all_findings if f.severity == "high"),
            "medium": sum(1 for f in all_findings if f.severity == "medium"),
            "low": sum(1 for f in all_findings if f.severity == "low"),
            "informational": sum(1 for f in all_findings if f.severity == "informational"),
            "total": len(all_findings),
            "memory_status": memory_status,
            "retained_memories": []
        }

        # Calculate final score
        score = ai_output.score
        if not ai_service.is_configured():
            score = max(0.0, 100.0 - (metrics["critical"] * 30 + metrics["high"] * 15 + metrics["medium"] * 8 + metrics["low"] * 3))

        # 7. Store review in database
        review_record = Review(
            project_id=project_id,
            user_id=user_id,
            title=title,
            language=language,
            source_code=source_code,
            file_path=file_path,
            status="completed",
            score=round(score, 1),
            summary=ai_output.summary,
            metrics=metrics,
            recalled_memories=[m.model_dump() for m in recalled_raw],
        )
        db.add(review_record)
        db.flush()

        # 8. Store findings in database
        for f in all_findings:
            finding_record = ReviewFinding(
                review_id=review_record.id,
                finding_id=f.finding_id,
                title=f.title,
                category=f.category,
                severity=f.severity,
                file_path=f.file_path,
                line_start=f.line_start,
                line_end=f.line_end,
                explanation=f.explanation,
                why_it_matters=f.why_it_matters,
                suggested_fix=f.suggested_fix,
                corrected_code=f.corrected_code,
                confidence=f.confidence,
                memory_references=f.memory_references,
            )
            db.add(finding_record)

        # 9. Retain useful, validated findings in Hindsight Cloud
        # Only retain findings that are either AST-verified or high-confidence critical/high issues.
        # Never store unverified AI guesses as facts.
        retained_list = []
        static_titles = {sf.get("title", "").lower().strip() for sf in static_findings}
        validated_findings = [
            f for f in all_findings
            if (f.title.lower().strip() in static_titles) or (f.confidence >= 0.90 and f.severity in ("critical", "high"))
        ]

        for vf in validated_findings[:3]:  # Limit to top 3 validated issues to avoid noisy banks
            lesson_content = (
                f"Project Finding ({vf.category.upper()}): {vf.title}. "
                f"Why it matters: {vf.why_it_matters} "
                f"Required fix: {vf.suggested_fix}"
            )
            cat = "vulnerabilities" if vf.category == "security" else ("recurring_bugs" if vf.category == "bug" else "coding_standards")
            try:
                mem_id = memory_service.retain_memory(
                    project_id=project_id,
                    content=lesson_content,
                    category=cat,
                    context=f"Auto-validated from review #{review_record.id} in {file_path}",
                    tags=[vf.category, vf.severity, f"project_{project_id}"]
                )
                if mem_id:
                    retained_list.append(f"{vf.title} ({vf.severity.upper()})")
                    logger.info(f"Retained validated finding into project {project_id} memory bank: {mem_id}")
            except Exception as e:
                logger.warning(f"Could not auto-retain finding '{vf.title}' in Hindsight: {e}")

        # Update review metrics with retained items
        metrics["retained_memories"] = retained_list
        review_record.metrics = metrics

        db.commit()
        db.refresh(review_record)

        return review_record

    def format_review_response(self, review: Review) -> ReviewResponse:
        recalled_items = []
        if review.recalled_memories:
            for item in review.recalled_memories:
                if isinstance(item, dict):
                    recalled_items.append(RecalledMemoryItem(**item))

        findings_schemas = []
        for f in review.findings:
            findings_schemas.append(
                FindingSchema(
                    finding_id=f.finding_id,
                    title=f.title,
                    category=f.category,
                    severity=f.severity,
                    file_path=f.file_path,
                    line_start=f.line_start,
                    line_end=f.line_end,
                    explanation=f.explanation,
                    why_it_matters=f.why_it_matters,
                    suggested_fix=f.suggested_fix,
                    corrected_code=f.corrected_code,
                    confidence=f.confidence,
                    memory_references=f.memory_references or []
                )
            )

        metrics = dict(review.metrics or {})
        retained_mems = metrics.get("retained_memories", [])
        mem_status = metrics.get("memory_status", "active")

        return ReviewResponse(
            id=review.id,
            project_id=review.project_id,
            user_id=review.user_id,
            title=review.title,
            language=review.language,
            source_code=review.source_code,
            file_path=review.file_path or "main",
            status=review.status,
            score=review.score,
            summary=review.summary,
            metrics=metrics,
            recalled_memories=recalled_items,
            retained_memories=retained_mems,
            memory_status=mem_status,
            findings=findings_schemas,
            created_at=review.created_at
        )

review_service = ReviewService()
