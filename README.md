\# QueueScale

\### Intelligent Queue-Based Traffic Management and Auto-Scaling System for Cloud-Native Applications



\## Overview



QueueScale is a cloud-native application designed to manage incoming registration requests through asynchronous message processing and automatic worker scaling.



The system uses RabbitMQ to buffer incoming requests and KEDA to dynamically scale Kubernetes worker replicas according to queue length. Prometheus collects application and infrastructure metrics, while Grafana provides real-time monitoring and visualization.



\## Architecture



The system consists of the following components:



\- \*\*FastAPI:\*\* Provides REST APIs for registration submission and status tracking.

\- \*\*PostgreSQL:\*\* Stores registration details and processing status.

\- \*\*RabbitMQ:\*\* Handles asynchronous message queuing.

\- \*\*Python Background Worker:\*\* Processes queued registration requests.

\- \*\*Docker:\*\* Containerizes the application services.

\- \*\*Kubernetes:\*\* Orchestrates API and worker deployments.

\- \*\*KEDA:\*\* Automatically scales background workers based on RabbitMQ queue length.

\- \*\*Prometheus:\*\* Collects application, RabbitMQ and Kubernetes metrics.

\- \*\*Grafana:\*\* Visualizes system performance and resource utilization.



\## System Workflow



1\. A client submits a registration request through the FastAPI endpoint.

2\. The API stores the registration in PostgreSQL.

3\. A message is published to the RabbitMQ registration queue.

4\. KEDA monitors queue length and adjusts the number of Kubernetes worker replicas.

5\. Background workers consume and process queued messages.

6\. PostgreSQL is updated with the final registration status.

7\. Prometheus collects metrics and Grafana displays system activity.



\## Technology Stack



| Category | Technologies |

|---|---|

| Backend | Python, FastAPI |

| Database | PostgreSQL |

| Message Broker | RabbitMQ |

| Containerization | Docker |

| Orchestration | Kubernetes |

| Autoscaling | KEDA |

| Monitoring | Prometheus, Grafana |

| Benchmarking | Python, CSV, Matplotlib |



\## Project Structure



```text

QueueScale/

├── app/

│   ├── \_\_init\_\_.py

│   ├── database.py

│   ├── models.py

│   ├── messaging.py

│   ├── main.py

│   └── worker.py

├── k8s/

│   ├── namespace.yaml

│   ├── api-deployment.yaml

│   ├── api-service.yaml

│   ├── worker-deployment.yaml

│   ├── scaled-object.yaml

│   ├── rabbitmq-trigger-auth.yaml

│   └── rabbitmq-scrape.yaml

├── references/

├── benchmark.py

├── generate\_graphs.py

├── architecture.mmd

├── architecture.png

├── docker-compose.yml

├── Dockerfile

├── requirements.txt

├── fixed\_workers\_benchmark\_50.csv

├── keda\_benchmark\_50.csv

├── keda\_dashboard\_test\_50.csv

├── keda\_benchmark\_100.csv

├── average\_completion\_latency.png

├── p95\_completion\_latency.png

├── average\_submission\_latency.png

└── README.md

```



\## Prerequisites



\- Docker Desktop

\- Docker Desktop Kubernetes

\- kubectl

\- Helm

\- Python 3.8 or later

\- KEDA

\- Prometheus and Grafana



\## Setup and Execution



\### 1. Clone the repository



```bash

git clone <YOUR\_GITHUB\_REPOSITORY\_URL>

cd QueueScale

```



\### 2. Configure environment variables



Create a `.env` file using the required PostgreSQL and RabbitMQ configuration.



Do not commit credentials or secrets to version control.



\### 3. Start PostgreSQL and RabbitMQ



```bash

docker compose -p queuescale up -d postgres rabbitmq

```



\### 4. Build application images



```bash

docker build -t queuescale-api:latest .

docker build -t queuescale-worker:latest .

```



\### 5. Deploy Kubernetes resources



Apply the Kubernetes manifests in the required order, including the namespace, application deployments, service, RabbitMQ authentication and KEDA ScaledObject.



Ensure that KEDA and the required monitoring components are installed and configured.



\### 6. Access the API



```bash

kubectl port-forward service/queuescale-api 8001:8000 -n queuescale

```



API health endpoint:



```text

http://localhost:8001/health

```



\### 7. Access Grafana



```bash

kubectl port-forward -n monitoring svc/queuescale-monitoring-grafana 3000:80

```



Open:



```text

http://localhost:3000

```



\## Performance Evaluation



The system was evaluated using fixed-worker and KEDA-based configurations.



\### Benchmark Results



| Configuration | Requests | Successful | Failed | Average Completion (s) | P95 Completion (s) |

|---|---:|---:|---:|---:|---:|

| Fixed 2 Workers | 50 | 50 | 0 | 9.514 | 10.524 |

| KEDA | 50 | 50 | 0 | 15.546 | 24.438 |

| KEDA Dashboard Test | 50 | 50 | 0 | 11.565 | 19.882 |

| KEDA | 100 | 100 | 0 | 20.547 | 42.785 |



All four experiments achieved a 100% registration completion rate.



\### Performance Graphs



The following graphs are generated from benchmark CSV files:



\- `average\_completion\_latency.png`

\- `p95\_completion\_latency.png`

\- `average\_submission\_latency.png`



\### Monitoring Dashboard



Grafana provides eight monitoring panels:



1\. RabbitMQ Queue Depth

2\. RabbitMQ Unacknowledged Messages

3\. RabbitMQ Active Consumers

4\. API Request Rate

5\. API Average Response Latency

6\. Kubernetes Worker Replicas

7\. Kubernetes Container CPU Usage

8\. Kubernetes Container Memory Usage



\## Key Features



\- Asynchronous request processing.

\- Queue-based traffic management.

\- Dynamic Kubernetes worker autoscaling.

\- Scale-to-zero capability.

\- Persistent registration records in PostgreSQL.

\- Real-time monitoring and visualization.

\- Benchmark-based performance evaluation.



\## Future Enhancements



\- Bounded message retries.

\- Dead Letter Queue (DLQ).

\- Idempotent message processing.

\- Improved failure recovery.

\- Extended workload testing and resource optimization.



\## Conclusion



QueueScale demonstrates how message queues, container orchestration and event-driven autoscaling can be integrated to manage workloads in cloud-native applications.



The implementation demonstrates asynchronous processing, automatic worker scaling, monitoring and performance evaluation under different workload configurations.

