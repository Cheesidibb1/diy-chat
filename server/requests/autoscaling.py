# pip install kubernetes
from kubernetes import client, config

# Load kube config (from default location or cluster)
config.load_kube_config()  # Use config.load_incluster_config() if running inside a pod

api = client.AppsV1Api()

# Define namespace and deployment name
namespace = "default"
deployment_name = "chatrequestserver"

# Function to scale deployment
def scale_deployment(replicas):
    body = {"spec": {"replicas": replicas}}
    api.patch_namespaced_deployment_scale(deployment_name, namespace, body)
    print(f"Scaled {deployment_name} to {replicas} replicas.")

# Example: Scale to 3 replicas
scale_deployment(3)
