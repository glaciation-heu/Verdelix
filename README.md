# Verdelix
Secure data management framework for AI 

Verdelix is a synthesis of two core concepts:

Verde: Derived from the Spanish and Italian word for "green," which implies environmental, sustainable, or eco-friendly connotations.

Helix: A term used to describe the spiral structure of a double-stranded DNA molecule in biology. The helix can metaphorically represent structure, continuity, and interwoven elements. In a broader sense, it may signify intertwined data or a structured approach.

Together, Verdelix suggests an eco-friendly, structured, and possibly intertwined or integrated approach, especially when applied to data or technology. It carries both an environmental consciousness and a sense of intricate, yet structured design. The name encapsulates the idea of a sustainable, green approach to structured or complex systems.
# Description of Verdelix
Verdelix, so far, is made up of two components. SODA and CEPH. To install SODA you firstly need to download the SODA installer

## To install SODA
git clone https://github.com/sodafoundation/installer.git
cd installer/ansible
Checkout the required version. For example, to checkout v1.9.0 follow
git checkout v1.9.0
chmod +x install\_dependencies.sh && source install\_dependencies.sh
export PATH=$PATH:/home/$USER/.local/bin

Running the install dependencies script must be done with root access

Next step is 

Set Host IP address - Set the environment variable HOST\_IP by using the steps below.

export HOST\_IP={your\_real\_host\_ip}
echo $HOST\_IP 
In the SODA Installer, modify host\_ip in group\_vars/common.yml and change it to the actual machine IP of the host.
By default the host\_ip is set to 127.0.0.1 i.e. localhost.

This field indicates local machine host ip
host\_ip: 127.0.0.1


## Install CEPH
Install the Rook Operator:
1. kubectl create -f https://raw.githubusercontent.com/rook/rook/release-1.7/cluster/examples/kubernetes/ceph/common.yaml
2. kubectl create -f https://raw.githubusercontent.com/rook/rook/release-1.7/cluster/examples/kubernetes/ceph/operator.yaml

Ensure the Rook Ceph operator pods are Running:
1. kubectl -n rook-ceph get pod
2. Deploy the Ceph Cluster:

Create a Ceph cluster:
1. kubectl create -f https://raw.githubusercontent.com/rook/rook/release-1.7/cluster/examples/kubernetes/ceph/cluster.yaml

This will create a minimal Ceph cluster with a single OSD (Object Storage Daemon) backed by a local directory. For production, you'd want to customize the cluster.yaml to your needs, especially the storage configuration.

Deploy the Rook Toolbox (Optional but useful for debugging and management):
1. kubectl create -f https://raw.githubusercontent.com/rook/rook/release-1.7/cluster/examples/kubernetes/ceph/toolbox.yaml


Once the toolbox is running, you can exec into the pod:
1. kubectl -n rook-ceph exec -it $(kubectl -n rook-ceph get pod -l "app=rook-ceph-tools" -o jsonpath='{.items[0].metadata.name}') bash


Inside the toolbox, you can use the ceph command to manage and monitor the Ceph cluster:
1. ceph status


Storage Class:
Rook provides a CephBlockPool and a StorageClass to integrate with Kubernetes PVCs:
1. kubectl create -f https://raw.githubusercontent.com/rook/rook/release-1.7/cluster/examples/kubernetes/ceph/csi/rbd/storageclass.yaml


After creating the storage class, you can define PersistentVolumeClaims in your applications, and Rook will ensure the storage is provisioned in the Ceph cluster.

Cleanup (If you ever need to delete the Ceph cluster):
1. kubectl delete -f https://raw.githubusercontent.com/rook/rook/release-1.7/cluster/examples/kubernetes/ceph/cluster.yaml
2. kubectl delete -f https://raw.githubusercontent.com/rook/rook/release-1.7/cluster/examples/kubernetes/ceph/operator.yaml
3. kubectl delete -f https://raw.githubusercontent.com/rook/rook/release-1.7/cluster/examples/kubernetes/ceph/common.yaml
