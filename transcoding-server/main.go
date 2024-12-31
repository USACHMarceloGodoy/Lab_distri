package main

import (
	"context"
	"fmt"
	"log"
	"os"
	"os/exec"
	"os/signal"

	"github.com/IBM/sarama"
)

// STRUCTS:
type Publisher struct {
	StreamKey string `json:"stream_key"`
}

type ConsumerGroupHandler struct{}

// FUNCIONES:
func (ConsumerGroupHandler) Setup(sarama.ConsumerGroupSession) error   { return nil }
func (ConsumerGroupHandler) Cleanup(sarama.ConsumerGroupSession) error { return nil }
func (ConsumerGroupHandler) ConsumeClaim(session sarama.ConsumerGroupSession, claim sarama.ConsumerGroupClaim) error {
	for message := range claim.Messages() {
		streamKey := string(message.Value)
		log.Printf("Mensaje recibido: %s", streamKey)
		go startTranscoding(streamKey)
		session.MarkMessage(message, "")
	}
	return nil
}

// Inicia la transcodificación para un stream específico utilizando  ffmpeg
func startTranscoding(streamKey string) {
	inputStream := fmt.Sprintf("rtmp://rtmp-server:1935/app/%s", streamKey)
	folderName := fmt.Sprintf("/srv/nfs/%s", streamKey)
	if _, err := os.Stat(folderName); os.IsNotExist(err) {
		os.Mkdir(folderName, 0755)
	}

	outputFile := fmt.Sprintf("%s/%s", folderName, streamKey)

	cmd := exec.Command("ffmpeg", "-i", inputStream, "-vcodec", "libx264", "-acodec", "aac", "-f", "hls", "-hls_time", "10", "-hls_list_size", "6", "-hls_segment_filename", outputFile+"_%03d.ts", outputFile+".m3u8")
	cmd.Stdout = os.Stdout
	cmd.Stderr = os.Stderr

	err := cmd.Run()
	if err != nil {
		log.Fatalf("Error al ejecutar ffmpeg para %s: %v", streamKey, err)
	}

	fmt.Printf("Transcodificación a HLS completada para el stream: %s.\n", streamKey)
}

func main() {
	// Configuración de Kafka
	config := sarama.NewConfig()
	config.Consumer.Group.Rebalance.Strategy = sarama.BalanceStrategyRoundRobin
	config.Version = sarama.V2_5_0_0

	brokers := []string{"kafka:9093"}
	topic := "transcoder-updates"
	consumerGroup := "example-group"

	consumer, err := sarama.NewConsumerGroup(brokers, consumerGroup, config)
	if err != nil {
		log.Fatalf("Error al crear el grupo consumidor: %v", err)
	}
	defer consumer.Close()

	ctx, cancel := context.WithCancel(context.Background())
	signals := make(chan os.Signal, 1)
	signal.Notify(signals, os.Interrupt)

	handler := ConsumerGroupHandler{}
	go func() {
		for {
			err := consumer.Consume(ctx, []string{topic}, handler)
			if err != nil {
				log.Printf("Error al consumir mensajes: %v", err)
			}

			if ctx.Err() != nil {
				return
			}
		}
	}()

	log.Println("Esperando mensajes...")
	<-signals
	cancel()
	log.Println("Consumidor terminado")
}
