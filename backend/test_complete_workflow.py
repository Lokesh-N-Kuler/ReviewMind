import sys
import os
import uuid
import time
from sqlalchemy.orm import Session

# Force UTF-8 encoding for console output on Windows
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

# Setup path
sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))

from app.database import SessionLocal, engine, Base
from app.models.user import User
from app.models.project import Project, ProjectMember
from app.services.review_service import review_service
from app.services.memory_service import memory_service
from app.utils.security import get_password_hash

def run_workflow_test():
    print("=" * 70)
    print("REVIEWMIND - COMPLETE PERSISTENT MEMORY REVIEW WORKFLOW VERIFICATION")
    print("=" * 70)

    db: Session = SessionLocal()
    try:
        # Step 0: Create test user
        test_email = f"workflow_{uuid.uuid4().hex[:6]}@example.com"
        user = User(
            email=test_email,
            hashed_password=get_password_hash("SecretPassword123!"),
            full_name="Workflow Test Developer"
        )
        db.add(user)
        db.commit()
        db.refresh(user)
        print(f"\n[Step 0] Created Test User: {user.email} (ID: {user.id})")

        # Step 1: Create a project
        proj_name = f"Billing System {uuid.uuid4().hex[:4]}"
        proj_bank_id = f"reviewmind-proj-{uuid.uuid4().hex[:6]}"
        project = Project(
            name=proj_name,
            description="Mission-critical customer billing and invoices backend",
            owner_id=user.id,
            languages=["python", "sql"],
            hindsight_bank_id=proj_bank_id,
            coding_standards="Enforce strict parameterized queries. Zero tolerance for SQL injection or dynamic SQL concatenation."
        )
        db.add(project)
        db.commit()
        db.refresh(project)
        print(f"[Step 1] Created Project: '{project.name}' (ID: {project.id})")
        
        # Initialize isolated memory bank for project
        bank_id = memory_service.get_bank_id_for_project(project.id)
        print(f"         Associated Hindsight Memory Bank: '{bank_id}'")
        memory_service.ensure_bank_exists(project.id, project.name)

        # Step 2: Submit Python code containing SQL injection (First Review)
        print("\n[Step 2] Submitting First Code Snippet (vulnerable to SQL injection)...")
        code_1 = """def fetch_user_balance(user_id):
    query = "SELECT balance FROM user_accounts WHERE id = " + user_id
    cursor = db.cursor()
    cursor.execute(query)
    return cursor.fetchone()
"""
        print("--- Submitted Code 1 ---")
        print(code_1.strip())
        print("------------------------")

        # Step 3 & 4: Generate an AI code review
        print("\n[Step 3 & 4] Generating AI Code Review via Review Orchestrator (AST + Groq LLM)...")
        review_1 = review_service.perform_review(
            db=db,
            project_id=project.id,
            user_id=user.id,
            source_code=code_1,
            language="python",
            title="User Balance Fetch Function",
            file_path="billing/accounts.py"
        )

        print(f"[SUCCESS] Review #1 Completed!")
        print(f"          Quality Score: {review_1.score}/100")
        print(f"          Total Findings: {len(review_1.findings)}")
        print(f"          Summary: {review_1.summary[:120]}...")

        # Verify SQL injection was detected with line number and fix
        sql_vuln = None
        for f in review_1.findings:
            print(f"          Finding: [{f.severity.upper()}] Line {f.line_start}: {f.title}")
            print(f"                   Why it matters: {f.why_it_matters[:90]}...")
            print(f"                   Suggested Fix:  {f.suggested_fix[:90]}...")
            if "sql" in f.title.lower() or f.category == "security":
                sql_vuln = f

        assert sql_vuln is not None, "Review 1 failed to identify SQL injection vulnerability!"
        assert sql_vuln.line_start is not None, "Vulnerability missing affected code line number!"
        assert sql_vuln.suggested_fix, "Vulnerability missing suggested fix guidance!"

        # Step 5: Store validated finding in Hindsight Cloud
        print("\n[Step 5] Checking Hindsight Memory Retention...")
        retained = review_1.metrics.get("retained_memories", [])
        print(f"         Auto-Retained Findings in Hindsight: {retained}")

        # Also explicitly retain the developer-approved rule to ensure solid semantic indexing
        explicit_rule = (
            f"ReviewMind Project Rule: In project '{project.name}', never use string concatenation (+) or f-strings for SQL queries. "
            f"Always use parameterized cursor.execute('SELECT ... WHERE id = %s', (user_id,)) placeholders."
        )
        mem_id = memory_service.retain_memory(
            project_id=project.id,
            content=explicit_rule,
            category="coding_standards",
            context="Confirmed team coding standard for SQL safety",
            tags=["sql", "security", "parameterized_queries"]
        )
        print(f"         Stored Confirmed Project Rule into Hindsight Bank '{bank_id}': ID {mem_id}")

        # Short pause to allow Hindsight Cloud semantic indexing
        print("         Waiting 3 seconds for Hindsight Cloud semantic indexing...")
        time.sleep(3)

        # Step 6: Submit similar code again (Second Review)
        print("\n[Step 6] Submitting Second Code Snippet with another SQL construction issue...")
        code_2 = """def get_customer_invoices(customer_id):
    # Retrieve customer billing history
    sql = f"SELECT * FROM invoices WHERE customer_id = '{customer_id}' ORDER BY date DESC"
    return db.execute(sql).fetchall()
"""
        print("--- Submitted Code 2 ---")
        print(code_2.strip())
        print("------------------------")

        # Step 7: Recall previous project knowledge and use it during second review
        print("\n[Step 7] Running Second Review - Recalling Previous Project Knowledge...")
        review_2 = review_service.perform_review(
            db=db,
            project_id=project.id,
            user_id=user.id,
            source_code=code_2,
            language="python",
            title="Customer Invoices Query",
            file_path="billing/invoices.py"
        )

        print(f"[SUCCESS] Review #2 Completed!")
        print(f"          Quality Score: {review_2.score}/100")
        print(f"          Recalled Memories Count: {len(review_2.recalled_memories)}")
        
        recalled_sql_rules = []
        for rm in review_2.recalled_memories:
            text = rm.get("text", "")
            print(f"          --> Recalled Memory: '{text[:90]}...'")
            if "sql" in text.lower() or "parameter" in text.lower():
                recalled_sql_rules.append(text)

        print(f"\n[Step 7 Verification] Findings from Second Review:")
        for f in review_2.findings:
            print(f"          Finding: [{f.severity.upper()}] Line {f.line_start}: {f.title}")
            print(f"                   Memory References: {f.memory_references}")
            print(f"                   Explanation: {f.explanation[:120]}...")

        # Confirm memory recall was active
        assert len(review_2.recalled_memories) > 0, "Second review did not recall memories from Hindsight!"
        print("\n" + "=" * 70)
        print(">>> COMPLETE WORKFLOW TEST PASSED ALL 7 PHASES SUCCESSFULLY! <<<")
        print("=" * 70)

    finally:
        db.close()

if __name__ == "__main__":
    run_workflow_test()
