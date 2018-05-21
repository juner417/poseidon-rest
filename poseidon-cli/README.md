# Poseidon-cli

## versions
- python :2.7

## usage
```bash
$ posecil
(apiserver:port)>> use http://localhost:8000
http://localhot:8000>> help
Poseidon Cli v0.1
>> cmd resource [args]

[cmd]
  use    : select poseidon rest api
  set    : select cluster
  gen    : generate json file
  read   : read json file
  create : create resource
  update : update resource
  list   : listing resource
  delete : delete resource
[resource]
  cluster
  node
  component
```


### list resource
```bash
>> list cluster
res: True
out: {'master': '172.19.136.122', 'name': 'ntest', 'uuid': 'cluster-5a21d2a3'}
out: {'master': '172.19.136.202', 'name': 'test-cluster', 'uuid': 'cluster-1b8b2cdc'}
out: {'master': '10.10.10.202', 'name': 'test-cluster1', 'uuid': 'cluster-14b8cdda'}

>> list node
res: True
out: {'status': 'plain', 'cluster': 'cluster-bb53713b', 'name': 'k8s-nminion-04', 'uuid': 'node-4d20c335'}
out: {'status': 'running', 'cluster': 'cluster-5a21d2a3', 'name': 'test', 'uuid': 'node-347aa3ff'}

>> list node cluster-bb53713b
res: True
out: {'status': 'plain', 'cluster': 'cluster-bb53713b', 'name': 'k8s-nminion-04', 'uuid': 'node-4d20c335'}
out: {'status': 'plain', 'cluster': 'cluster-bb53713b', 'name': 'k8s-nminion-05', 'uuid': 'node-dbaf6c0d'}
```

### create node
```bash
>> gen node node.out
res: True
out: node-183520.json

>> create node node-183520.json
res: True
out: {'k8s-nminion-04': 0}
out: {'k8s-nminion-05': 1}
out: {'k8s-nminion-04': 'node-4d20c335'}
out: {'k8s-nminion-05': 'node-dbaf6c0d'}
```

### update node status
```bash
>> update node status install
```
