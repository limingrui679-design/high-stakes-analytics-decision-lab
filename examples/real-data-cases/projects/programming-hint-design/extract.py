"""Use the published challenge evaluation and an independent source of real novice errors."""

import ast
import csv
import io
import zipfile


def modifies_while_traversing(tree):
    for loop in ast.walk(tree):
        if isinstance(loop, ast.For) and isinstance(loop.iter, ast.Name):
            for node in ast.walk(loop):
                if (
                    isinstance(node, ast.Call)
                    and isinstance(node.func, ast.Attribute)
                    and node.func.attr == "remove"
                    and isinstance(node.func.value, ast.Name)
                    and node.func.value.id == loop.iter.id
                ):
                    return True
    return False


def rows(src):
    with zipfile.ZipFile(src.get("CSEDM-6e7a1f6463d6343bd0c063fdeacf9cf9147e5073.zip")) as z:
        name = next(k for k in z.namelist() if k.endswith("/Example/cv_predict.csv"))
        for r in csv.DictReader(io.TextIOWrapper(z.open(name), encoding="utf-8")):

            def b(key, r=r):
                return int(r[key].upper() == "TRUE")

            yield (
                "challenge/" + r["SubjectID"] + "/" + r["ProblemID"],
                "CSEDM",
                r["SubjectID"],
                r["ProblemID"],
                r["StartOrder"],
                b("FirstCorrect"),
                b("UsedHint"),
                r["Attempts"],
                r["priorPercentCorrect"],
                r["priorAttempts"],
                b("prediction"),
                r["fold"],
                "",
                "",
                "",
            )
    with zipfile.ZipFile(src.get("refactory.zip")) as outer:
        with zipfile.ZipFile(
            io.BytesIO(outer.read(next(k for k in outer.namelist() if k.endswith("/data.zip"))))
        ) as z:
            for name in sorted(
                k
                for k in z.namelist()
                if "/question_3/code/" in k
                and k.endswith(".py")
                and any(t in k for t in ["/wrong/", "/correct/"])
            ):
                source = z.read(name).decode("utf-8", errors="replace")
                try:
                    tree = ast.parse(source)
                    pattern = int(modifies_while_traversing(tree))
                except SyntaxError:
                    pattern = ""
                short = name.rsplit("/", 1)[-1]
                yield (
                    "refactory/" + short,
                    "Refactory",
                    "",
                    "remove_extras",
                    "",
                    "",
                    "",
                    "",
                    "",
                    "",
                    "",
                    "",
                    short,
                    int("/correct/" in name),
                    pattern,
                )
