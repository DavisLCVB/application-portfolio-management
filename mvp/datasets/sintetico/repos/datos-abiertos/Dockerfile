FROM eclipse-temurin:17-jre-alpine
WORKDIR /app
COPY target/datos-abiertos.jar app.jar
ENTRYPOINT ["java", "-jar", "app.jar"]
