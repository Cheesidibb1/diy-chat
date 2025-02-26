# pip install kubernetes
from kubernetes import client, config

# Load kube config (from default location or cluster)
config.load_kube_config()  # Use config.load_incluster_config() if running inside a pod

api = client.AppsV1Api()

# Define namespace and deployment name
namespace = "default"
deployment_name = "chatrequestserver-deployment"  # Updated to match the deployment.yaml

# Function to scale deployment
def scale_deployment(replicas):
    try:
        replicas = int(replicas)
        body = {"spec": {"replicas": replicas}}
        api.patch_namespaced_deployment_scale(deployment_name, namespace, body)
        print(f"Scaled {deployment_name} to {replicas} replicas.")
    except ValueError:
        print("Invalid number of replicas. Please enter an integer.")
    except client.exceptions.ApiException as e:
        if e.status == 404:
            print(f"Deployment {deployment_name} not found in namespace {namespace}.")
        else:
            print(f"An error occurred: {e}")

# Example: Scale to user-specified replicas
cheese = input("Enter the number of replicas: ")
scale_deployment(cheese)
