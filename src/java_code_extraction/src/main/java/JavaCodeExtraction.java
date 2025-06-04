import com.github.javaparser.StaticJavaParser;
import com.github.javaparser.ast.CompilationUnit;
import com.github.javaparser.ast.body.MethodDeclaration;
import com.github.javaparser.ast.stmt.BlockStmt;
import com.github.javaparser.ast.ImportDeclaration;

import java.io.File;
import java.io.IOException;
import java.nio.charset.StandardCharsets;
import java.nio.file.Files;
import java.nio.file.Paths;
import java.util.Optional;
import java.util.List;

public class JavaCodeExtraction {

    public static String getMethodSourceCode(String filePath, String methodName) throws IOException {
        File file = new File(filePath);
        CompilationUnit cu = StaticJavaParser.parse(file);
        Optional<MethodDeclaration> methodOpt = cu.findFirst(
                MethodDeclaration.class,
                m -> m.getNameAsString().equals(methodName)
        );
        return methodOpt.map(MethodDeclaration::toString).orElse(null);
    }

    public static void replaceMethodBodyAndImports(String filePath, String methodName, String newFilePath) throws IOException {
        // Parse the original file to be modified
        CompilationUnit targetCU = StaticJavaParser.parse(new File(filePath));
        Optional<MethodDeclaration> targetMethodOpt = targetCU.findFirst(MethodDeclaration.class,
                m -> m.getNameAsString().equals(methodName));
        if (targetMethodOpt.isEmpty()) {
            throw new RuntimeException("Target method '" + methodName + "' not found in " + filePath);
        }

        // Read and clean new file content
        String newFileContent = Files.readString(Paths.get(newFilePath), StandardCharsets.UTF_8);
        newFileContent = newFileContent.replaceFirst("(?m)^\\s*package\\s+[^;]+;\\s*", "").trim();

        // Wrap top-level method and imports inside a dummy class if necessary
        boolean hasClass = newFileContent.contains("class");
        if (!hasClass) {
            // Extract import lines
            StringBuilder imports = new StringBuilder();
            StringBuilder body = new StringBuilder();
            for (String line : newFileContent.split("\\R")) {
                if (line.trim().startsWith("import ")) {
                    imports.append(line).append("\n");
                } else {
                    body.append(line).append("\n");
                }
            }

            newFileContent = imports + "\npublic class DummyWrapper {\n" + body + "\n}";
        }

        // Always parse as CompilationUnit
        CompilationUnit newCU = StaticJavaParser.parse(newFileContent);

        // Extract method and body
        MethodDeclaration newMethod = newCU.findFirst(MethodDeclaration.class)
                                           .orElseThrow(() -> new RuntimeException("No method found in new file"));
        BlockStmt newBody = newMethod.getBody()
                                     .orElseThrow(() -> new RuntimeException("Parsed method has no body"));

        // Replace imports if any
        List<ImportDeclaration> newImports = newCU.getImports();
        if (!newImports.isEmpty()) {
            targetCU.getImports().clear();
            targetCU.getImports().addAll(newImports);
        }

        // Replace method body
        targetMethodOpt.get().setBody(newBody);

        // Save back the updated file
        Files.write(Paths.get(filePath), targetCU.toString().getBytes(StandardCharsets.UTF_8));
    }

    public static void main(String[] args) throws Exception {
        if (args.length < 3) {
            System.err.println("Usage:\n" +
                "  java JavaCodeExtraction print   <filePath> <methodName>\n" +
                "  java JavaCodeExtraction replace <filePath> <methodName> (uses optimized_java.txt)");
            System.exit(1);
        }

        String operation = args[0];
        String filePath = args[1];
        String methodName = args[2];

        switch (operation.toLowerCase()) {
            case "print":
                String source = getMethodSourceCode(filePath, methodName);
                System.out.println(source == null ? "Method not found" : source);
                break;

            case "replace":
                String blockPath = "../../../runtime_logs/optimized_java.txt";
                System.out.println("=== Original Method Source ===");
                System.out.println(getMethodSourceCode(filePath, methodName));

                replaceMethodBodyAndImports(filePath, methodName, blockPath);

                System.out.println("=== Replaced Method Source ===");
                System.out.println(getMethodSourceCode(filePath, methodName));
                break;

            default:
                System.err.println("Unknown operation: " + operation);
                System.exit(1);
        }
    }
}
