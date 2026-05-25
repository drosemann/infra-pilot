package com.playerservers;

import java.io.File;
import java.io.FileWriter;
import java.io.IOException;

public class ServerPropertiesGenerator {

    public static void generate(File serverDirectory, String serverName) {
        File propertiesFile = new File(serverDirectory, "server.properties");
        try (FileWriter writer = new FileWriter(propertiesFile)) {
            writer.write("server-ip=127.0.0.1\n");
            writer.write("server-port=25565\n");
            writer.write("query.port=25565\n");
            writer.write("rcon.port=25575\n");
            writer.write("enable-query=false\n");
            writer.write("enable-rcon=false\n");
            writer.write("level-seed=\n");
            writer.write("gamemode=survival\n");
            writer.write("enable-command-block=false\n");
            writer.write("max-players=20\n");
            writer.write("motd=Player Server: " + serverName + "\n");
            writer.write("pvp=true\n");
            writer.write("difficulty=easy\n");
            writer.write("enable-status=true\n");
            writer.write("online-mode=false\n");
            writer.write("white-list=false\n");
            writer.write("level-type=DEFAULT\n");
            writer.write("spawn-animals=true\n");
            writer.write("spawn-npcs=true\n");
            writer.write("allow-flight=false\n");
            writer.write("resource-pack=\n");
            writer.write("level-name=world\n");
            writer.write("server-id=" + serverName + "\n");
        } catch (IOException e) {
            e.printStackTrace();
        }
    }
}
