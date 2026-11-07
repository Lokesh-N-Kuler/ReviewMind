import ast
import re
from typing import List, Dict, Any, Optional

class StaticFinding:
    def __init__(
        self,
        finding_id: str,
        title: str,
        category: str,
        severity: str,
        line_start: Optional[int],
        line_end: Optional[int],
        explanation: str,
        why_it_matters: str,
        suggested_fix: str,
        confidence: float = 0.95
    ):
        self.finding_id = finding_id
        self.title = title
        self.category = category
        self.severity = severity
        self.line_start = line_start
        self.line_end = line_end
        self.explanation = explanation
        self.why_it_matters = why_it_matters
        self.suggested_fix = suggested_fix
        self.confidence = confidence

    def to_dict(self) -> Dict[str, Any]:
        return {
            "finding_id": self.finding_id,
            "title": self.title,
            "category": self.category,
            "severity": self.severity,
            "line_start": self.line_start,
            "line_end": self.line_end,
            "explanation": self.explanation,
            "why_it_matters": self.why_it_matters,
            "suggested_fix": self.suggested_fix,
            "confidence": self.confidence,
        }

class PythonASTAnalyzer(ast.NodeVisitor):
    def __init__(self, code: str):
        self.code = code
        self.findings: List[StaticFinding] = []
        self._counter = 1

    def _next_id(self) -> str:
        fid = f"STATIC-PY-{self._counter:03d}"
        self._counter += 1
        return fid

    def visit_Call(self, node: ast.Call):
        func_name = ""
        if isinstance(node.func, ast.Name):
            func_name = node.func.id
        elif isinstance(node.func, ast.Attribute):
            func_name = node.func.attr

        # 1. Check eval / exec
        if func_name in ("eval", "exec"):
            self.findings.append(
                StaticFinding(
                    finding_id=self._next_id(),
                    title=f"Dangerous dynamic code execution using `{func_name}()`",
                    category="security",
                    severity="critical",
                    line_start=node.lineno,
                    line_end=getattr(node, "end_lineno", node.lineno),
                    explanation=f"Direct invocation of `{func_name}()` evaluates arbitrary input as executable Python code.",
                    why_it_matters="Arbitrary code execution allows attackers to run unauthorized commands or compromise the host.",
                    suggested_fix=f"Replace `{func_name}()` with safe domain-specific parsing (e.g., `ast.literal_eval`, `json.loads`).",
                    confidence=0.98
                )
            )

        # 2. Check subprocess with shell=True
        if func_name in ("Popen", "run", "call", "check_output", "check_call"):
            for kw in node.keywords:
                if kw.arg == "shell" and isinstance(kw.value, ast.Constant) and kw.value.value is True:
                    self.findings.append(
                        StaticFinding(
                            finding_id=self._next_id(),
                            title="Command Injection risk: `shell=True` in subprocess invocation",
                            category="security",
                            severity="critical",
                            line_start=node.lineno,
                            line_end=getattr(node, "end_lineno", node.lineno),
                            explanation="Spawning a subshell with `shell=True` processes shell metacharacters and enables command injection.",
                            why_it_matters="If external parameters are interpolated into the command string, attackers can execute arbitrary shell commands.",
                            suggested_fix="Pass commands as a list of strings and set `shell=False`.",
                            confidence=0.95
                        )
                    )

        # 3. Check os.system
        if isinstance(node.func, ast.Attribute) and isinstance(node.func.value, ast.Name):
            if node.func.value.id == "os" and node.func.attr == "system":
                self.findings.append(
                    StaticFinding(
                        finding_id=self._next_id(),
                        title="Unsafe system command execution via `os.system`",
                        category="security",
                        severity="high",
                        line_start=node.lineno,
                        line_end=getattr(node, "end_lineno", node.lineno),
                        explanation="`os.system()` passes strings directly to the platform shell without escaping.",
                        why_it_matters="Prone to command injection when concatenated with user-controlled input.",
                        suggested_fix="Use `subprocess.run([args], check=True, shell=False)` instead.",
                        confidence=0.95
                    )
                )

        # 4. Check pickle.loads
        if isinstance(node.func, ast.Attribute) and isinstance(node.func.value, ast.Name):
            if node.func.value.id == "pickle" and node.func.attr in ("load", "loads"):
                self.findings.append(
                    StaticFinding(
                        finding_id=self._next_id(),
                        title="Insecure deserialization via `pickle`",
                        category="security",
                        severity="critical",
                        line_start=node.lineno,
                        line_end=getattr(node, "end_lineno", node.lineno),
                        explanation="The `pickle` module is not secure against erroneous or maliciously constructed data.",
                        why_it_matters="Unpickling untrusted data can execute arbitrary code during object reconstruction.",
                        suggested_fix="Use a safer serialization format such as JSON, Protocol Buffers, or HMAC-signed tokens.",
                        confidence=0.95
                    )
                )

        self.generic_visit(node)

    def visit_BinOp(self, node: ast.BinOp):
        # Check string concatenation in SQL queries
        if isinstance(node.op, ast.Add):
            left_is_sql = self._is_sql_string(node.left)
            right_is_sql = self._is_sql_string(node.right)
            if left_is_sql or right_is_sql:
                self.findings.append(
                    StaticFinding(
                        finding_id=self._next_id(),
                        title="SQL Injection: Raw SQL query constructed via string concatenation (`+`)",
                        category="security",
                        severity="critical",
                        line_start=node.lineno,
                        line_end=getattr(node, "end_lineno", node.lineno),
                        explanation="SQL statements formed by concatenating variables directly bypass parameter escaping.",
                        why_it_matters="Attackers can alter query logic, dump database tables, or execute administrative SQL commands.",
                        suggested_fix="Use parameterized queries (e.g. `cursor.execute('SELECT * FROM users WHERE id = %s', (user_id,))`) or an ORM.",
                        confidence=0.98
                    )
                )
        self.generic_visit(node)

    def visit_JoinedStr(self, node: ast.JoinedStr):
        # Check f-strings containing SQL syntax
        raw_parts = []
        has_expressions = False
        for value in node.values:
            if isinstance(value, ast.Constant) and isinstance(value.value, str):
                raw_parts.append(value.value)
            elif isinstance(value, ast.FormattedValue):
                has_expressions = True

        combined_text = " ".join(raw_parts).upper()
        if has_expressions and any(kw in combined_text for kw in ("SELECT ", "INSERT INTO ", "UPDATE ", "DELETE FROM ", "DROP TABLE ")):
            self.findings.append(
                StaticFinding(
                    finding_id=self._next_id(),
                    title="SQL Injection: SQL query formed using f-string interpolation",
                    category="security",
                    severity="critical",
                    line_start=node.lineno,
                    line_end=getattr(node, "end_lineno", node.lineno),
                    explanation="Dynamically embedding variables into SQL text via f-strings causes SQL injection.",
                    why_it_matters="User input can break out of string delimiters and execute arbitrary SQL operations.",
                    suggested_fix="Use parameterized queries with query placeholders (`?`, `%s`, `:param`) provided separately to the database driver.",
                    confidence=0.95
                )
            )
        self.generic_visit(node)

    def visit_ExceptHandler(self, node: ast.ExceptHandler):
        # Check empty or bare except
        if node.type is None or (isinstance(node.type, ast.Name) and node.type.id in ("Exception", "BaseException")):
            # Check if body is just `pass`
            if len(node.body) == 1 and isinstance(node.body[0], ast.Pass):
                self.findings.append(
                    StaticFinding(
                        finding_id=self._next_id(),
                        title="Silent Exception Suppression (`except: pass`)",
                        category="error_handling",
                        severity="medium",
                        line_start=node.lineno,
                        line_end=getattr(node, "end_lineno", node.lineno),
                        explanation="Swallowing all exceptions with `pass` hides critical failures, bugs, and keyboard interrupts.",
                        why_it_matters="Makes bugs and unexpected crashes impossible to diagnose and masks system failures.",
                        suggested_fix="Catch specific exception classes and log the error trace properly.",
                        confidence=0.9
                    )
                )
        self.generic_visit(node)

    def _is_sql_string(self, node: ast.AST) -> bool:
        if isinstance(node, ast.Constant) and isinstance(node.value, str):
            val = node.value.upper()
            return any(k in val for k in ("SELECT ", "INSERT INTO ", "UPDATE ", "DELETE FROM ", "WHERE ", "FROM "))
        return False

def analyze_code_statically(code: str, language: str) -> List[Dict[str, Any]]:
    findings: List[Dict[str, Any]] = []
    lang = language.lower().strip()

    # Generic checks: Hardcoded secrets across all languages
    secret_patterns = [
        (r'(?i)(api[_-]?key|secret[_-]?key|access[_-]?token|auth[_-]?token|private[_-]?key)\s*[:=]\s*["\']([a-zA-Z0-9_\-]{16,})["\']', "Potential Hardcoded Secret / API Key", "security", "high"),
        (r'(?i)password\s*[:=]\s*["\'][^"\']{4,}["\']', "Hardcoded Password Literal", "security", "high"),
    ]

    lines = code.split("\n")
    counter = 1
    for i, line in enumerate(lines, 1):
        for pattern, title, category, severity in secret_patterns:
            if re.search(pattern, line):
                findings.append({
                    "finding_id": f"STATIC-SECRET-{counter:03d}",
                    "title": title,
                    "category": category,
                    "severity": severity,
                    "line_start": i,
                    "line_end": i,
                    "explanation": "Credentials and secret keys should not be checked into source code.",
                    "why_it_matters": "Exposing secrets in code leads to credential leaks and repository compromise.",
                    "suggested_fix": "Extract the credential into an environment variable or secure secrets manager.",
                    "confidence": 0.88,
                })
                counter += 1

    # Python-specific AST checks
    if lang in ("python", "py"):
        try:
            tree = ast.parse(code)
            visitor = PythonASTAnalyzer(code)
            visitor.visit(tree)
            for f in visitor.findings:
                findings.append(f.to_dict())
        except SyntaxError as e:
            findings.append({
                "finding_id": "SYNTAX-ERR-001",
                "title": f"Python Syntax Error: {e.msg}",
                "category": "bug",
                "severity": "high",
                "line_start": e.lineno,
                "line_end": e.lineno,
                "explanation": f"Source code fails to parse as valid Python: {e.msg}",
                "why_it_matters": "Code with syntax errors will fail at compile/runtime immediately.",
                "suggested_fix": "Correct the syntax error at the indicated line.",
                "confidence": 1.0,
            })

    # JavaScript / TypeScript static checks
    elif lang in ("javascript", "typescript", "js", "ts", "jsx", "tsx"):
        for i, line in enumerate(lines, 1):
            if re.search(r'\beval\s*\(', line):
                findings.append({
                    "finding_id": f"STATIC-JS-{counter:03d}",
                    "title": "Unsafe `eval()` execution",
                    "category": "security",
                    "severity": "critical",
                    "line_start": i,
                    "line_end": i,
                    "explanation": "`eval()` parses strings as executable JavaScript in the current execution context.",
                    "why_it_matters": "Opens severe Cross-Site Scripting (XSS) or Remote Code Execution vulnerabilities.",
                    "suggested_fix": "Refactor to use structured object lookup or JSON.parse().",
                    "confidence": 0.95
                })
                counter += 1
            if re.search(r'innerHTML\s*=', line):
                findings.append({
                    "finding_id": f"STATIC-JS-{counter:03d}",
                    "title": "DOM-based XSS via `innerHTML` assignment",
                    "category": "security",
                    "severity": "high",
                    "line_start": i,
                    "line_end": i,
                    "explanation": "Assigning unescaped text to `innerHTML` allows script tags and HTML injection.",
                    "why_it_matters": "Attackers can execute malicious scripts in users' browsers.",
                    "suggested_fix": "Use `textContent`, `innerText`, or sanitize using DOMPurify.",
                    "confidence": 0.92
                })
                counter += 1

    # SQL static checks
    elif lang in ("sql",):
        for i, line in enumerate(lines, 1):
            if re.search(r'(?i)SELECT\s+\*\s+FROM', line):
                findings.append({
                    "finding_id": f"STATIC-SQL-{counter:03d}",
                    "title": "Use of `SELECT *` in production query",
                    "category": "performance",
                    "severity": "low",
                    "line_start": i,
                    "line_end": i,
                    "explanation": "`SELECT *` fetches all columns, including large text or unused fields.",
                    "why_it_matters": "Increases I/O, network bandwidth, memory consumption, and breaks index-only scans.",
                    "suggested_fix": "Specify only the explicit columns needed by the application.",
                    "confidence": 0.85
                })
                counter += 1

    return findings
