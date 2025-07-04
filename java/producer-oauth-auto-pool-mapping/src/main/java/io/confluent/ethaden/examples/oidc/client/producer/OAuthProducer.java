package io.confluent.ethaden.examples.oidc.client.producer;

import java.io.FileInputStream;
import java.io.FileNotFoundException;
import java.io.IOException;
import java.lang.invoke.MethodHandles;
import java.util.Properties;
import java.util.Random;
import org.apache.kafka.clients.producer.KafkaProducer;
import org.apache.kafka.clients.producer.ProducerConfig;
import org.apache.kafka.clients.producer.ProducerRecord;
import org.apache.kafka.clients.producer.RecordMetadata;
import org.apache.kafka.common.serialization.StringSerializer;
import org.apache.logging.log4j.LogManager;
import org.apache.logging.log4j.Logger;

public class OAuthProducer {

    private static final Logger LOGGER = LogManager.getLogger(MethodHandles.lookup().lookupClass());

    private int count = 0;
    private Properties settings = new Properties();
    private String topic;

    private void initSettings(String propertiesFile) throws FileNotFoundException, IOException {
        settings.load(new FileInputStream(propertiesFile));
        settings.put(ProducerConfig.KEY_SERIALIZER_CLASS_CONFIG, StringSerializer.class);
        settings.put(ProducerConfig.VALUE_SERIALIZER_CLASS_CONFIG, StringSerializer.class);
        this.topic = settings.getProperty("topic", "test");
        settings.remove("topic");
        // for (String key: settings.stringPropertyNames()) {
        //     String value = settings.getProperty(key);
        //     System.out.println(String.format("\"%s\"=\"%s\"", key, value));
        // }
    }
        
    public static void main(String[] args) {
        if (args.length != 1) {
            System.err.println("Usage: OAuthProducer <client.properties");
            System.exit(1);
        }
        OAuthProducer producer = new OAuthProducer(args[0]);
        producer.produce(10);
    }

    public OAuthProducer(String propertiesFile) {
        try {
            initSettings(propertiesFile);
        } catch (FileNotFoundException e) {
            LOGGER.error("Properties file not found: {}", propertiesFile, e);
            System.exit(1);
        } catch (IOException e) {
            LOGGER.error("Error reading properties file: {}", propertiesFile, e);
            System.exit(1);
        }
    }

    void produce(int nb) {
        LOGGER.info("Starting Arvo Producer");
        Random rand = new Random();
        try (KafkaProducer<String, String> producer = new KafkaProducer<>(this.settings)) {
            for (int i=0; i < nb; i++) {
                String key = Integer.toString(count);
                double randValue = rand.nextDouble(100);
                String value = Double.valueOf(randValue).toString();
                ProducerRecord<String, String> producerRecord = new ProducerRecord<>(this.topic, key, value);
                LOGGER.info("Sending message {}", count);
                producer.send(producerRecord, (RecordMetadata recordMetadata, Exception exception) -> {
                    if (exception == null) {
                        System.out.println("Record written to offset " +
                                recordMetadata.offset() + " timestamp " +
                                recordMetadata.timestamp());
                    } else {
                        System.err.println("An error occurred");
                        exception.printStackTrace(System.err);
                    }
              });
                count++;
            }
            LOGGER.info("Producer flush");
            producer.flush();
        } finally {
            LOGGER.info("Closing producer");
        }
    }
}
