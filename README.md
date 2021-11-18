### Context
[OpenShift's Elasticsearch Operator](https://github.com/openshift/elasticsearch-operator "OpenShift's Elasticsearch Operator") (version > 5.0) come with a set of Indexmanagement (IM) [scripts](https://github.com/openshift/elasticsearch-operator/blob/release-5.2/internal/indexmanagement/scripts.go "scripts"). These scripts are deployed as a configMap (configmap/indexmanagement-scripts) in the `openshift-logging` namespace. For instance:

    # oc get configmaps -n openshift-logging
    NAME                                   DATA   AGE
    cluster-logging-operator-lock          0      9d
    elasticsearch                          3      9d
    fluentd                                2      9d
    fluentd-trusted-ca-bundle              1      9d
    indexmanagement-scripts                8      84m  <==
    kibana-trusted-ca-bundle               1      9d
    kube-root-ca.crt                       1      9d
    openshift-service-ca.crt               1      9d

The operator deploys 3 cronJobs (running every 15 minutes) that uses these scripts for "Index Management" i.e, cleaning up the old indices that are no longer with in the window of retention (set in the elasticsearch CR). For instance:

    # oc get cronjobs -n openshift-logging
    NAME                     SCHEDULE       SUSPEND   ACTIVE   LAST SCHEDULE   AGE
    elasticsearch-im-app     */15 * * * *   False     0        4m55s           9d
    elasticsearch-im-audit   */15 * * * *   False     0        4m55s           9d
    elasticsearch-im-infra   */15 * * * *   False     0        4m55s           9d

### Problem

**On a prefectly healthy cluster** and under **ideal conditions**, these IM cronjobs would randomly fail once in a while. This is not serious as the succeeding cronjob runs would normally take care of anything missed by the previous failed job. However the randomly failing jobs generate alerts every now and then, which creates unnecessary alert fatigue. It is noted that in most of the cases, these randomly failing jobs would fail because of elasticsearch api call failing with the following error:

    {"error":{"root_cause":[{"type":"security_exception","reason":"_opendistro_security_dls_query does not match (SG 900D)"}],"type":"security_exception","reason":"_opendistro_security_dls_query does not match (SG 900D)"},"status":500}

### Debug Scripts

These debug scripts are modified to log debugging information when the cronjob/scripts runs. The debug information can help identify the root cause of these random but recurring failing jobs.

**Disclaimer: Do not try this in Production. Author takes no reponsibility whatsoever**

Following is the description of files/directories present in this repository:

- **indexmanagement-scripts-orig**: Set of original/unmodified IM scripts shipped with the operator (v5.2.2-21).
- **indexmanagement-scripts-debug-base**: Debugging scripts base (used by next two dirs).
- **indexmanagement-scripts-debug-always**: Debugging scripts with configMap. These scripts output debug information on every (successful or failed) run. 
- **indexmanagement-scripts-debug-onerror**: Debugging scripts with configMap. These scripts will only output debug information if the job fails.
- **im-debug-captures**: Some sample debug logs of failed jobs captured in a test cluster.

To use the debug scripts, create the configMap (from either indexmanagement-scripts-debug-onerror/ or indexmanagement-scripts-debug-always/) and then patch the cronjobs to use this configmap instead. For example:

    oc create -n openshift-logging -f indexmanagement-scripts-debug-onerror.cm.yaml
    
    oc patch -n openshift-logging cronjob/elasticsearch-im-app -p '{"spec": {"jobTemplate": {"spec": {"template": {"spec": {"volumes": [{"name": "scripts", "configMap": {"name": "indexmanagement-scripts-debug-onerror"}}]}}}}}}'
    oc patch -n openshift-logging cronjob/elasticsearch-im-infra -p '{"spec": {"jobTemplate": {"spec": {"template": {"spec": {"volumes": [{"name": "scripts", "configMap": {"name": "indexmanagement-scripts-debug-onerror"}}]}}}}}}'
    oc patch -n openshift-logging cronjob/elasticsearch-im-audit -p '{"spec": {"jobTemplate": {"spec": {"template": {"spec": {"volumes": [{"name": "scripts", "configMap": {"name": "indexmanagement-scripts-debug-onerror"}}]}}}}}}'


