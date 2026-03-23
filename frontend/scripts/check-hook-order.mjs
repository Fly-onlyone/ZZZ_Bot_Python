import { readdirSync, readFileSync, statSync } from "node:fs";
import path from "node:path";
import process from "node:process";
import { parse } from "@babel/parser";

const projectRoot = path.resolve(import.meta.dirname, "..");
const targetDirectories = ["src/pages", "src/content", "src/routes"];
const sourceExtensions = new Set([".js", ".jsx"]);

function isFunctionLike(node) {
  return (
    node?.type === "FunctionDeclaration" ||
    node?.type === "FunctionExpression" ||
    node?.type === "ArrowFunctionExpression"
  );
}

function isComponentName(name) {
  return typeof name === "string" && /^[A-Z]/.test(name);
}

function isHookCallee(callee) {
  if (!callee) {
    return false;
  }

  if (callee.type === "Identifier") {
    return /^use[A-Z0-9]/.test(callee.name);
  }

  if (
    callee.type === "MemberExpression" &&
    !callee.computed &&
    callee.object?.type === "Identifier" &&
    callee.object.name === "React" &&
    callee.property?.type === "Identifier"
  ) {
    return /^use[A-Z0-9]/.test(callee.property.name);
  }

  return false;
}

function visitNode(node, visitor) {
  if (!node || typeof node !== "object") {
    return;
  }

  if (visitor(node) === false) {
    return;
  }

  for (const value of Object.values(node)) {
    if (Array.isArray(value)) {
      for (const child of value) {
        visitNode(child, visitor);
      }
      continue;
    }

    visitNode(value, visitor);
  }
}

function expressionHasHookCall(expression) {
  let found = false;

  visitNode(expression, (node) => {
    if (found) {
      return false;
    }

    if (node !== expression && isFunctionLike(node)) {
      return false;
    }

    if (node.type === "CallExpression" && isHookCallee(node.callee)) {
      found = true;
      return false;
    }

    return true;
  });

  return found;
}

function statementHasTopLevelHookCall(statement) {
  if (!statement) {
    return false;
  }

  switch (statement.type) {
    case "VariableDeclaration":
      return statement.declarations.some((declaration) =>
        expressionHasHookCall(declaration.init)
      );
    case "ExpressionStatement":
      return expressionHasHookCall(statement.expression);
    case "IfStatement":
      return expressionHasHookCall(statement.test);
    default:
      return false;
  }
}

function firstDirectReturnLine(statement) {
  if (!statement) {
    return null;
  }

  switch (statement.type) {
    case "ReturnStatement":
      return statement.loc?.start.line ?? null;
    case "BlockStatement":
      for (const child of statement.body) {
        const line = firstDirectReturnLine(child);
        if (line != null) {
          return line;
        }
      }
      return null;
    case "IfStatement":
      return (
        firstDirectReturnLine(statement.consequent) ??
        firstDirectReturnLine(statement.alternate)
      );
    case "SwitchStatement":
      for (const switchCase of statement.cases) {
        for (const child of switchCase.consequent) {
          const line = firstDirectReturnLine(child);
          if (line != null) {
            return line;
          }
        }
      }
      return null;
    case "TryStatement":
      return (
        firstDirectReturnLine(statement.block) ??
        firstDirectReturnLine(statement.handler?.body) ??
        firstDirectReturnLine(statement.finalizer)
      );
    case "LabeledStatement":
      return firstDirectReturnLine(statement.body);
    default:
      return null;
  }
}

function inspectComponentFunction(name, body, filePath, violations) {
  if (!body || body.type !== "BlockStatement") {
    return;
  }

  let earlyReturnLine = null;

  for (const statement of body.body) {
    if (earlyReturnLine == null) {
      earlyReturnLine = firstDirectReturnLine(statement);
      continue;
    }

    if (statementHasTopLevelHookCall(statement)) {
      violations.push({
        filePath,
        componentName: name,
        earlyReturnLine,
        hookLine: statement.loc?.start.line ?? null,
      });
    }
  }
}

function inspectAst(ast, filePath, violations) {
  visitNode(ast, (node) => {
    if (node.type === "FunctionDeclaration" && isComponentName(node.id?.name)) {
      inspectComponentFunction(node.id.name, node.body, filePath, violations);
      return true;
    }

    if (
      node.type === "VariableDeclarator" &&
      node.id?.type === "Identifier" &&
      isComponentName(node.id.name) &&
      isFunctionLike(node.init)
    ) {
      inspectComponentFunction(
        node.id.name,
        node.init.body,
        filePath,
        violations
      );
    }

    return true;
  });
}

function collectSourceFiles(directoryPath, files) {
  for (const entry of readdirSync(directoryPath)) {
    const absolutePath = path.join(directoryPath, entry);
    const stats = statSync(absolutePath);

    if (stats.isDirectory()) {
      collectSourceFiles(absolutePath, files);
      continue;
    }

    if (sourceExtensions.has(path.extname(absolutePath))) {
      files.push(absolutePath);
    }
  }
}

function parseFile(filePath) {
  const source = readFileSync(filePath, "utf8");
  return parse(source, {
    sourceType: "module",
    plugins: ["jsx"],
    errorRecovery: false,
  });
}

const filesToCheck = [];

for (const relativeDirectory of targetDirectories) {
  collectSourceFiles(path.join(projectRoot, relativeDirectory), filesToCheck);
}

const violations = [];

for (const filePath of filesToCheck) {
  const ast = parseFile(filePath);
  inspectAst(ast, filePath, violations);
}

if (violations.length > 0) {
  console.error(
    "Hook-order check failed. Move hooks above any top-level early return in these components:"
  );

  for (const violation of violations) {
    const relativeFilePath = path.relative(projectRoot, violation.filePath);
    const earlyReturnSuffix =
      violation.earlyReturnLine != null ? `:${violation.earlyReturnLine}` : "";
    const hookSuffix =
      violation.hookLine != null ? `:${violation.hookLine}` : "";

    console.error(
      `- ${relativeFilePath}${hookSuffix} ${violation.componentName} declares a hook after an early return at ${relativeFilePath}${earlyReturnSuffix}`
    );
  }

  process.exit(1);
}

console.log(
  `Hook-order check passed for ${filesToCheck.length} frontend source files.`
);
