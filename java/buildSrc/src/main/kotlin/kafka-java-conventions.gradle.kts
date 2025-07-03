plugins {
    id("java-common-conventions")
}

dependencies {
    implementation("org.apache.kafka:kafka-clients:8.0.0-ce")
    //implementation("io.confluent:kafka-streams-avro-serde:8.0.0")
}
