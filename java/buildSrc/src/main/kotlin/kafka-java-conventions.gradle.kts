plugins {
    id("java-common-conventions")
}

dependencies {
    implementation("org.apache.kafka:kafka-clients:8.0.0-ce")
    implementation("com.fasterxml.jackson.module:jackson-module-kotlin:2.19.+")
}
