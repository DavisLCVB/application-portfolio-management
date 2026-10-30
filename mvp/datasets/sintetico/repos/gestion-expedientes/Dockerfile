FROM eclipse-temurin:17-jre-alpine
WORKDIR /app
COPY target/gestion-expedientes.jar app.jar
ENTRYPOINT ["java", "-jar", "app.jar"]
