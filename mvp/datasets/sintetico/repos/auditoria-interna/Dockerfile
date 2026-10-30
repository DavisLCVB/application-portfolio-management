FROM eclipse-temurin:17-jre-alpine
WORKDIR /app
COPY target/auditoria-interna.jar app.jar
ENTRYPOINT ["java", "-jar", "app.jar"]
