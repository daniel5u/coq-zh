using Microsoft.CodeAnalysis;
using Microsoft.CodeAnalysis.CSharp;
using Microsoft.CodeAnalysis.CSharp.Syntax;
using System.Text.Json;
using System.Text.RegularExpressions;

if (args.Length != 2) throw new ArgumentException("Usage: TextCatalogue SOURCE_DIRECTORY OUTPUT.jsonl");
string root = Path.GetFullPath(args[0]);
using var output = new StreamWriter(args[1]);
int files = 0, rows = 0, parseErrors = 0;
foreach (string file in Directory.EnumerateFiles(root, "*.cs", SearchOption.AllDirectories).Order())
{
    files++;
    var tree = CSharpSyntaxTree.ParseText(File.ReadAllText(file));
    parseErrors += tree.GetDiagnostics().Count(d => d.Severity == DiagnosticSeverity.Error);
    foreach (SyntaxNode node in tree.GetRoot().DescendantNodes())
    {
        string? text = null, kind = null;
        var holes = new List<string>();
        if (node is LiteralExpressionSyntax literal && literal.Token.Value is string value)
        { text = value; kind = "literal"; }
        else if (node is InterpolatedStringExpressionSyntax interpolated)
        {
            text = string.Concat(interpolated.Contents.Select(part => part is InterpolatedStringTextSyntax t ? t.TextToken.ValueText : Hole(part)));
            kind = "interpolation";
        }
        else if (node is BinaryExpressionSyntax binary && binary.IsKind(SyntaxKind.AddExpression) &&
                 !(binary.Parent is BinaryExpressionSyntax parent && parent.IsKind(SyntaxKind.AddExpression)))
        {
            var parts = Flatten(binary).ToList();
            if (!parts.Any(p => p is LiteralExpressionSyntax l && l.Token.Value is string)) continue;
            text = string.Concat(parts.Select(p => p is LiteralExpressionSyntax l && l.Token.Value is string v ? v : Hole(p)));
            kind = "concatenation-candidate"; // '+' can also add numbers: requires human review.
        }
        if (text == null || string.IsNullOrWhiteSpace(text)) continue;
        var argument = node.Ancestors().OfType<ArgumentSyntax>().FirstOrDefault();
        var invocation = argument?.Parent?.Parent as InvocationExpressionSyntax;
        string call = invocation?.Expression.ToString() ?? "";
        int argumentIndex = invocation == null ? -1 : invocation.ArgumentList.Arguments.IndexOf(argument!);
        string member = node.Ancestors().OfType<MethodDeclarationSyntax>().FirstOrDefault()?.Identifier.ValueText ?? "";
        string variable = node.Ancestors().OfType<VariableDeclaratorSyntax>().FirstOrDefault()?.Identifier.ValueText ?? "";
        string classification = "unclassified";
        if (Regex.IsMatch(call, @"(?:^|\.)(?:_S|_T)$")) classification = argumentIndex == 0 ? "localization-key" : "localized-call-argument";
        else if (Regex.IsMatch(call, @"(?:Popup\.(?:Show\w*|Ask\w*)|MessageQueue\.AddPlayerMessage)$") && argumentIndex == 0)
            classification = "display-candidate";
        else if (Regex.IsMatch(variable, @"^(?:options|choices|menuOptions)$", RegexOptions.IgnoreCase) ||
                 Regex.IsMatch(member, @"^Get(?:Description|LevelText|CreateCharacterDisplayName)$")) classification = "display-candidate";
        else if (Regex.IsMatch(text, @"\b[A-Za-z]{2,}[ ,!?]+[A-Za-z]{2,}\b")) classification = "prose-candidate";
        output.WriteLine(JsonSerializer.Serialize(new {
            file = Path.GetRelativePath(root, file), line = node.GetLocation().GetLineSpan().StartLinePosition.Line + 1,
            kind, src = text, holes, call, argumentIndex, member, classification,
            expression = kind == "literal" ? null : node.ToString()
        }));
        rows++;
        string Hole(SyntaxNode expression) { int id = holes.Count; holes.Add(expression.ToString()); return "{" + id + "}"; }
    }
}
Console.WriteLine(JsonSerializer.Serialize(new { files, rows, parseErrors }));

static IEnumerable<ExpressionSyntax> Flatten(ExpressionSyntax expression)
{
    if (expression is BinaryExpressionSyntax b && b.IsKind(SyntaxKind.AddExpression))
    { foreach (var e in Flatten(b.Left)) yield return e; foreach (var e in Flatten(b.Right)) yield return e; }
    else yield return expression;
}
