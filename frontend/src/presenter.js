/**
 * Takes a raw resource object and returns a structured, human-readable summary.
 */
export function presentResource(resource) {
  const resourceType = resource?.resource_type?.toLowerCase();
  const data = resource?.data || {};

  const presenters = {
    'deployment': presentDeployment,
    'service': presentService,
    'secret': presentSecret,
    'ingress': presentIngress,
    'configmap': presentConfigMap,
    'pod': presentPod,
    'persistentvolume': presentPersistentVolume,
    'persistentvolumeclaim': presentPersistentVolumeClaim,
    'statefulset': presentStatefulSet,
    'daemonset': presentDaemonSet,
    'job': presentJob,
    'cronjob': presentCronJob,
    'horizontalpodautoscaler': presentHPA,
    'customresourcedefinition': presentCRD,
    'networkpolicy': presentNetworkPolicy,
  };

  const presenterFunc = presenters[resourceType];
  if (presenterFunc) {
    return presenterFunc(data);
  }

  return { "Info": "No specific summary view available for this resource type.", "Data": data };
}

function presentDeployment(data) {
  const spec = data.spec || {};
  const status = data.status || {};
  return {
    "Replicas": `${status.readyReplicas || 0} / ${spec.replicas || 0}`,
    "Strategy": spec.strategy?.type || 'N/A',
    "Containers": (spec.template?.spec?.containers || []).map(c => ({ Name: c.name, Image: c.image })),
    "Conditions": (status.conditions || []).map(c => `${c.type}: ${c.status}`),
  };
}

function presentService(data) {
  const spec = data.spec || {};
  return {
    "Type": spec.type,
    "Cluster IP": spec.clusterIP,
    "Ports": (spec.ports || []).map(p => `${p.name || ''} ${p.port}:${p.targetPort}/${p.protocol}`.trim()),
    "Selector": spec.selector || 'None',
  };
}

function presentSecret(data) {
  return { "Type": data.type, "Data Keys": Object.keys(data.data || {}) };
}

function presentIngress(data) {
    const spec = data.spec || {};
    return {
        "Ingress Class": spec.ingressClassName || 'None',
        "Rules": (spec.rules || []).map(rule => ({
            Host: rule.host,
            Paths: (rule.http?.paths || []).map(p => `${p.path} ➔ ${p.backend.service?.name}:${p.backend.service?.port?.number || p.backend.service?.port?.name}`),
        })),
    };
}

function presentConfigMap(data) {
    return data.data || {};
}

function presentPod(data) {
    const spec = data.spec || {};
    const status = data.status || {};
    return {
        "Status": status.phase,
        "Node": spec.nodeName,
        "IP": status.podIP,
        "Containers": (spec.containers || []).map(c => ({
            Name: c.name,
            Image: c.image,
            Ready: (status.containerStatuses?.find(cs => cs.name === c.name)?.ready ?? false).toString()
        }))
    };
}

function presentPersistentVolume(data) {
    const spec = data.spec || {};
    return {
        "Capacity": spec.capacity?.storage,
        "Access Modes": spec.accessModes,
        "Reclaim Policy": spec.persistentVolumeReclaimPolicy,
        "Status": data.status?.phase,
        "Claim": spec.claimRef?.name,
        "Storage Class": spec.storageClassName,
    };
}

function presentPersistentVolumeClaim(data) {
    const spec = data.spec || {};
    return {
        "Status": data.status?.phase,
        "Volume": spec.volumeName,
        "Capacity": data.status?.capacity?.storage,
        "Access Modes": spec.accessModes,
        "Storage Class": spec.storageClassName,
    };
}

function presentStatefulSet(data) {
    const spec = data.spec || {};
    return {
        "Replicas": `${data.status?.readyReplicas || 0} / ${spec.replicas || 0}`,
        "Service Name": spec.serviceName,
        "Update Strategy": spec.updateStrategy?.type,
    };
}

function presentDaemonSet(data) {
    const status = data.status || {};
    return {
        "Desired": status.desiredNumberScheduled,
        "Current": status.currentNumberScheduled,
        "Ready": status.numberReady,
        "Available": status.numberAvailable,
    };
}

function presentJob(data) {
    return {
        "Completions": data.spec?.completions,
        "Parallelism": data.spec?.parallelism,
        "Succeeded": data.status?.succeeded,
        "Failed": data.status?.failed,
    };
}

function presentCronJob(data) {
    return {
        "Schedule": data.spec?.schedule,
        "Suspend": data.spec?.suspend,
        "Last Schedule": data.status?.lastScheduleTime,
    };
}

function presentHPA(data) {
    const spec = data.spec || {};
    return {
        "Scale Target": `${spec.scaleTargetRef.kind}/${spec.scaleTargetRef.name}`,
        "Min Replicas": spec.minReplicas,
        "Max Replicas": spec.maxReplicas,
        "Current Replicas": data.status?.currentReplicas,
    };
}

function presentCRD(data) {
    const spec = data.spec || {};
    return {
        "Group": spec.group,
        "Scope": spec.scope,
        "Versions": (spec.versions || []).map(v => v.name),
    };
}

function presentNetworkPolicy(data) {
    return {
        "Pod Selector": data.spec?.podSelector,
        "Policy Types": data.spec?.policyTypes,
    };
}