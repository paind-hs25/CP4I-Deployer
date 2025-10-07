# CP4I Deployer
This repository contains all the necessary resources in order to deploy IBM Cloud Pak for Integration (CP4I) fully automated on an OpenShift Cluster in a GitOps manner.

## Prerequisites
* Obtain an OCP Cluster. You can provision a cluster on [Techzone](https://techzone.ibm.com/collection/tech-zone-certified-base-images/journey-vmware-on-ibm-cloud-environments).
* You've installed the `oc`command on your local machine.

## Set up your repository
In order to use deploy the CP4I effectively, it is the easiest if you use your own copy of the repository. 

### 1. Fork this repository
Create a Fork in your personal GitHub-account by clicking the `Fork` button:

<img src=images/image.png alt="Fork button" width="200"/>

### 2. Clone your forked repository on your local machine
Change to a folder where you wanna clone the repository in and execute:

```
git clone https://github.com/<your-github-username>/<your-repo-name>.git
```

### 3. Set the repoURL in the ArgoCD applications
In order that the CP4I can be deployed to OpenShift in a GitOps manner, ArgoCD needs to now where the ressources,which in monitors, are stored. Therefore we need to set our repoURL in ArgoCD applications.

1. Set the environment variable `REPO_URL`:

    ```bash
    export REPO_URL="https://github.com/<your-github-username>/<your-repo-name>.git"
    ```
2. Run the script `set-repo-url.sh` in the scripts folder. **Make sure your in the root-folder** of the repository and run:
    ```bash
    ./scripts/set-repo-url.sh
    ```

    If the script run successfully the terminal output should be: `🎉 All repoURLs were successfully set`

3. Commit and push the changes to GitHub:
    ```bash
    git commit -am "set the repoURL in all ArgoCD apps"
    git push origin main
    ```

## Installing custom ArgoCD
When provisioning a cluster via IBM Techzone, then the GitOps-Operator is installed per default and with that a default ArgoCD instance. This default instance isn't sufficient for us, since we need e.g. additional health checks in order that ArgoCD can monitor our CP4I ressources. Therefore we gonna deploy a custom ArgoCD instance:

1. Log in to your Openshift Cluster on the cli:
    ```bash
    oc login --token=<token> --server=<server>
    ```

2. Delete the default ArgoCD instance:
    ```bash
    oc delete gitopsservice cluster || true
    ````

3. Create ClusterRole and ClusterRoleBinding in order to allow the custom ArgoCD instance to manage the appropriate namespaces and resources:
    ```bash
    oc apply -f setup/
    ```

4. Create the custom ArgoCD instance:
    ```bash
    oc apply -f setup/argocd-instance/argocd-instance.yaml
    ```
    Wait until the ArgoCD instance is ready. The following command will wait until the ArgoCD instance is ready:
    ```bash
    while ! oc wait pod --timeout=-1s --for=condition=ContainersReady -l app.kubernetes.io/name=openshift-gitops-custom-server -n openshift-gitops > /dev/null; do sleep 30; done
    ```

## Obtain the IBM Entitlement Key and create the secret in OpenShift
In order to be able to pull the CP4I images from the IBM Entitled Registry, you need to obtain the IBM Entitlement Key. You have to login to [MyIBM Container Software Library](https://myibm.ibm.com/products-services/containerlibrary) with your IBMID and then you can find create and copy your entitlement key.

Next you need to create a secret in the `openshift-operators` namespace with your entitlement key. Issue the following command with your entitlement key passed as the `--docker-password` parameter:

```bash
oc create secret docker-registry ibm-entitlement-key \
    --docker-username=cp \
    --docker-password=<your-ibm-entitlement-key> \
    --docker-server=cp.icr.io \
    --namespace=openshift-operators
```