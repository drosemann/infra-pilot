FROM maven:3.9-eclipse-temurin-8 AS build

WORKDIR /app
COPY pom.xml .
RUN mvn dependency:go-offline -B

COPY src ./src
RUN mvn -B clean package -DskipTests

FROM eclipse-temurin:8-jre-alpine

WORKDIR /app
RUN apk add --no-cache tzdata

COPY --from=build /app/target/*.jar ./plugin.jar

VOLUME ["/data"]
ENTRYPOINT ["java", "-jar", "plugin.jar"]
