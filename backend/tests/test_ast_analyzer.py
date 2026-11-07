from app.utils.ast_parser import analyze_code_statically

def test_sql_injection_concatenation():
    code = """
def get_user(user_id):
    query = "SELECT * FROM users WHERE id = " + user_id
    return db.execute(query)
"""
    findings = analyze_code_statically(code, "python")
    sql_findings = [f for f in findings if "SQL" in f["title"]]
    assert len(sql_findings) >= 1
    f = sql_findings[0]
    assert f["category"] == "security"
    assert f["severity"] == "critical"
    assert f["line_start"] == 3

def test_sql_injection_fstring():
    code = """
def search_items(name):
    sql = f"SELECT * FROM items WHERE name = '{name}'"
    return execute(sql)
"""
    findings = analyze_code_statically(code, "python")
    sql_findings = [f for f in findings if "SQL" in f["title"]]
    assert len(sql_findings) >= 1
    assert sql_findings[0]["severity"] == "critical"

def test_dangerous_eval():
    code = """
def calculate(expr):
    return eval(expr)
"""
    findings = analyze_code_statically(code, "python")
    eval_findings = [f for f in findings if "eval" in f["title"]]
    assert len(eval_findings) >= 1
    assert eval_findings[0]["severity"] == "critical"

def test_subprocess_shell_true():
    code = """
import subprocess
def run_cmd(user_arg):
    subprocess.Popen(f"ls {user_arg}", shell=True)
"""
    findings = analyze_code_statically(code, "python")
    cmd_findings = [f for f in findings if "shell=True" in f["title"]]
    assert len(cmd_findings) >= 1

def test_hardcoded_secret():
    code = """
api_key = "sk_live_1234567890abcdef123456"
"""
    findings = analyze_code_statically(code, "python")
    secret_findings = [f for f in findings if "Secret" in f["title"]]
    assert len(secret_findings) >= 1

def test_javascript_inner_html_and_eval():
    code = """
function render(input) {
    document.getElementById('content').innerHTML = input;
    eval(input);
}
"""
    findings = analyze_code_statically(code, "javascript")
    assert any("innerHTML" in f["title"] for f in findings)
    assert any("eval" in f["title"] for f in findings)
