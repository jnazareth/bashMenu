import java.io.BufferedReader;
import java.io.IOException;
import java.io.InputStreamReader;
import java.util.LinkedHashMap;
import java.util.List;
import java.util.Map;

public class BashMenu {

    // ANSI color codes
    private static final String RED = "\u001B[31m";
    private static final String GREEN = "\u001B[32m";
    private static final String YELLOW = "\u001B[33m";
    private static final String BLUE = "\u001B[34m";
    private static final String CYAN = "\u001B[36m";
    private static final String NC = "\u001B[0m"; // No color

    private static List<String> bashMenuList = new java.util.ArrayList<>();

    private static void showUsage() {
        System.out.println(RED + "Usage: java BashMenu" + NC);
    }

    private static Map<String, String> readMenuList(String commandsFile) throws IOException {
        Map<String, String> commandMap = new LinkedHashMap<>();

        try (BufferedReader br = new BufferedReader(new java.io.FileReader(commandsFile))) {
            String line;
            while ((line = br.readLine()) != null) {
                line = line.trim();
                if (line.isEmpty() || line.startsWith("#")) {
                    continue; // skip empty lines or comments
                }

                // Split line into commandName and commandInstruction
                String[] parts = line.split("=", 2); // limit=2 ensures only first comma splits
                if (parts.length == 2) {
                    String commandName = parts[0].trim();
                    String commandInstruction = parts[1].trim();

                    commandMap.put(commandName, commandInstruction);
                } else {
                    System.err.println("Skipping invalid line: " + line);
                }
            }
        }

        return commandMap;
    }

    public static void main(String[] args) throws IOException {
        int parmNo;
        String commandsFile = "";

        if (args.length != 1) {
            BashMenu.showUsage();
            return;
        }

        for (parmNo = 0; parmNo < args.length; parmNo++) {
            if (parmNo == 0) commandsFile = args[parmNo] ;
        }
        Map<String, String> commandMap = readMenuList(commandsFile);
        buildMenu(commandMap);

        BufferedReader reader = new BufferedReader(new InputStreamReader(System.in));

        while (true) {
            clearScreen();
            showMenu();

            System.out.print("Enter your choice [1-" + (commandMap.size() + 1) + "]: ");
            String choice = reader.readLine();

            Integer i = Integer.valueOf(choice);
            if (i == Integer.valueOf(commandMap.size()+1)) {
                System.out.println(YELLOW + "Exiting..." + NC);
                pause(500);
                break;
            } else if (i <= 0 || i > Integer.valueOf(commandMap.size()+1)) {
                System.out.println(RED + "Invalid choice!" + NC);
                pause(500);
                continue;
            } else{
                String commandKey = (String) commandMap.keySet().toArray()[i-1];
                String commandInstruction = commandMap.get(commandKey);
                System.out.println(BLUE + "You selected: " + commandInstruction + NC);
                runInBash(commandInstruction);
            }

            // Pause after executing a choice
            System.out.print(YELLOW + "\nPress Enter to continue..." + NC);
            reader.readLine();
        }
    }

    private static void buildHeader() {
        bashMenuList.clear();
        bashMenuList.add(CYAN + "==============================" + NC);
        bashMenuList.add(YELLOW + "     Command Line Menu" + NC);
        bashMenuList.add(CYAN + "==============================" + NC);
    }

    private static int buildOptions(Map<String, String> commandMap) {
        bashMenuList.add("");
        int optionNumber = 1;

        // Iterate through the LinkedHashMap in insertion order
        for (Map.Entry<String, String> entry : commandMap.entrySet()) {
            String commandName = entry.getKey();
            String commandInstruction = entry.getValue();
            bashMenuList.add(GREEN + optionNumber + ")" + NC + " " + commandName + CYAN + " -> " + BLUE + commandInstruction + NC);
            optionNumber++;
        }

        return optionNumber;
    }

    private static void buildExitOption(int items) {
        bashMenuList.add(RED + "" + (items) + ")" + " Exit" + NC);
        bashMenuList.add("");
    }

    private static void buildMenu(Map<String, String> commandMap) {
        buildHeader();
        int items = buildOptions(commandMap);
        buildExitOption(items);
    }

    private static void showMenu() {
        for (String line : bashMenuList) {
            System.out.println(line);
        }
    }

    private static void runInBash(String command) {
        // Define the path to the bash executable
        // NOTE: Adjust the path based on your installation location
        String gitBashPath = "C:/Program Files/Git/bin/bash.exe";

        // Define the working directory (your Git repository path)
        String workingDirectory = ".";
        //String workingDirectory = "C:/Users/NazarethJ/Downloads/projects/bashMenu";

        // The command you want to run, passed as a single string to the -c argument
        String gitCommand = command;

        try {
            ProcessBuilder processBuilder = new ProcessBuilder();

            // Set the command: executable, -c flag, and the command string
            processBuilder.command(gitBashPath, "-c", gitCommand);

            // Set the working directory for the command
            processBuilder.directory(new java.io.File(workingDirectory));

            // Redirect error stream to the standard output stream so we can read both
            processBuilder.redirectErrorStream(true);

            // Start the process
            Process process = processBuilder.start();

            // Read the output from the process
            BufferedReader reader = new BufferedReader(new InputStreamReader(process.getInputStream()));
            String line;
            StringBuilder output = new StringBuilder();
            while ((line = reader.readLine()) != null) {
                output.append(line).append(System.getProperty("line.separator"));
            }

            // Wait for the process to complete
            int exitVal = process.waitFor();

            if (exitVal == 0) {
                System.out.println("--- Command run successfully ---");
                System.out.println("Output:\n" + output.toString());
            } else {
                System.out.println("--- Command run unsuccessfully ---");
                System.out.println("Error output:\n" + output.toString());
            }

        } catch (IOException | InterruptedException e) {
            System.out.println("--- Exception occurred ---");
            e.printStackTrace();
            // Restore interrupted state
            Thread.currentThread().interrupt();
        }
    }

    private static void clearScreen() {
        System.out.print("\033[H\033[2J");
        System.out.flush();
    }

    private static void pause(long millis) {
        try {
            Thread.sleep(millis);
        } catch (InterruptedException ignored) {
        }
    }
}