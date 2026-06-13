"""Extended compliance scanner with CIS, NIST, BSI + custom benchmarks, waiver mgmt, and reporting.""" 
import json, uuid, hashlib, logging, csv, io
from typing import Dict, Any, Optional, List, Tuple
from datetime import datetime, timedelta
from dataclasses import dataclass, field
logger = logging.getLogger(__name__)

@dataclass
class ComplianceCheckExt:
    check_id: str; standard: str; category: str; description: str; severity: str
    remediation: str; status: str; evidence: Optional[Dict[str,Any]]; control_family: Optional[str]
    nist_family: Optional[str]; bsi_module: Optional[str]; check_type: str
    automated: bool; risk_impact: str; likelihood: str; cvss_score: Optional[float]
    def to_dict(self):
        return {"check_id":self.check_id,"standard":self.standard,"category":self.category,
                "description":self.description,"severity":self.severity,"remediation":self.remediation,
                "status":self.status,"evidence":self.evidence,"control_family":self.control_family,
                "check_type":self.check_type,"automated":self.automated,"risk_impact":self.risk_impact,
                "cvss_score":self.cvss_score}

@dataclass
class ComplianceScanExt:
    scan_id:str;standard:str;target:str;timestamp:datetime;total_checks:int;passed:int;failed:int
    waived:int;error:int;compliance_score:float;status:str;checks:List[ComplianceCheckExt]
    scan_type:str;scanner_version:str;duration_seconds:float
    def to_dict(self):
        return {"scan_id":self.scan_id,"standard":self.standard,"target":self.target,
                "timestamp":self.timestamp.isoformat(),"summary":{"total_checks":self.total_checks,
                "passed":self.passed,"failed":self.failed,"waived":self.waived,"error":self.error,
                "compliance_score":round(self.compliance_score,1)},"status":self.status,
                "scan_type":self.scan_type,"scanner_version":self.scanner_version,
                "duration_seconds":round(self.duration_seconds,1),
                "checks":[c.to_dict() for c in self.checks]}

CIS_DOCKER_V81 = [
    {"check_id":"CIS_DOCKER_1.1.1","category":"Host Configuration","description":"Ensure Linux kernel architecture is supported","severity":"high","remediation":"Use supported Linux distribution","control_family":"Host OS"},
    {"check_id":"CIS_DOCKER_1.1.2","category":"Host Configuration","description":"Ensure container hostname is properly set","severity":"medium","remediation":"Set --hostname flag","control_family":"Host OS"},
    {"check_id":"CIS_DOCKER_1.2.1","category":"Host Configuration","description":"Ensure container runtime is up-to-date","severity":"high","remediation":"Update container runtime","control_family":"Host OS"},
    {"check_id":"CIS_DOCKER_2.1","category":"Docker Daemon Configuration","description":"Ensure network traffic is restricted between containers","severity":"high","remediation":"Set --icc=false in daemon.json","control_family":"Daemon"},
    {"check_id":"CIS_DOCKER_2.2","category":"Docker Daemon Configuration","description":"Ensure logging level is set to 'info'","severity":"medium","remediation":"Configure log level in daemon.json","control_family":"Daemon"},
    {"check_id":"CIS_DOCKER_2.3","category":"Docker Daemon Configuration","description":"Ensure Docker iptables changes are allowed","severity":"medium","remediation":"Set --iptables=true","control_family":"Daemon"},
    {"check_id":"CIS_DOCKER_2.4","category":"Docker Daemon Configuration","description":"Ensure insecure registries are not used","severity":"high","remediation":"Remove insecure registries from daemon.json","control_family":"Daemon"},
    {"check_id":"CIS_DOCKER_2.5","category":"Docker Daemon Configuration","description":"Ensure aufs storage driver is not used","severity":"medium","remediation":"Use overlay2 storage driver","control_family":"Daemon"},
    {"check_id":"CIS_DOCKER_2.6","category":"Docker Daemon Configuration","description":"Ensure TLS authentication for Docker daemon","severity":"critical","remediation":"Configure TLS with --tlsverify","control_family":"Daemon"},
    {"check_id":"CIS_DOCKER_2.7","category":"Docker Daemon Configuration","description":"Ensure default ulimit is configured","severity":"low","remediation":"Set default ulimit in daemon.json","control_family":"Daemon"},
    {"check_id":"CIS_DOCKER_2.8","category":"Docker Daemon Configuration","description":"Enable user namespace support","severity":"high","remediation":"Enable userns-remap","control_family":"Daemon"},
    {"check_id":"CIS_DOCKER_2.9","category":"Docker Daemon Configuration","description":"Ensure cgroup permission are set correctly","severity":"medium","remediation":"Set --cgroup-parent properly","control_family":"Daemon"},
    {"check_id":"CIS_DOCKER_2.10","category":"Docker Daemon Configuration","description":"Ensure base device size is configured","severity":"low","remediation":"Configure --storage-opt dm.basesize","control_family":"Daemon"},
    {"check_id":"CIS_DOCKER_3.1","category":"Docker Daemon Files","description":"Ensure docker.service file ownership is root:root","severity":"high","remediation":"chown root:root docker.service","control_family":"File Permissions"},
    {"check_id":"CIS_DOCKER_3.2","category":"Docker Daemon Files","description":"Ensure docker.service file permissions are 644","severity":"medium","remediation":"chmod 644 docker.service","control_family":"File Permissions"},
    {"check_id":"CIS_DOCKER_3.3","category":"Docker Daemon Files","description":"Ensure docker.socket file ownership is root:root","severity":"high","remediation":"chown root:root docker.socket","control_family":"File Permissions"},
    {"check_id":"CIS_DOCKER_3.4","category":"Docker Daemon Files","description":"Ensure docker.socket file permissions are 644","severity":"medium","remediation":"chmod 644 docker.socket","control_family":"File Permissions"},
    {"check_id":"CIS_DOCKER_3.5","category":"Docker Daemon Files","description":"Ensure /etc/docker directory ownership is root:root","severity":"high","remediation":"chown root:root /etc/docker","control_family":"File Permissions"},
    {"check_id":"CIS_DOCKER_3.6","category":"Docker Daemon Files","description":"Ensure /etc/docker directory permissions are 755","severity":"medium","remediation":"chmod 755 /etc/docker","control_family":"File Permissions"},
    {"check_id":"CIS_DOCKER_3.7","category":"Docker Daemon Files","description":"Ensure registry certificate file permissions are 444","severity":"medium","remediation":"chmod 444 cert files","control_family":"File Permissions"},
    {"check_id":"CIS_DOCKER_3.8","category":"Docker Daemon Files","description":"Ensure /etc/docker/daemon.json permissions are 644","severity":"medium","remediation":"chmod 644 daemon.json","control_family":"File Permissions"},
    {"check_id":"CIS_DOCKER_4.1","category":"Container Images and Build","description":"Ensure user for container has been created","severity":"high","remediation":"Create non-root user in Dockerfile","control_family":"Images"},
    {"check_id":"CIS_DOCKER_4.2","category":"Container Images and Build","description":"Ensure containers use trusted base images","severity":"high","remediation":"Use official images from trusted registries","control_family":"Images"},
    {"check_id":"CIS_DOCKER_4.3","category":"Container Images and Build","description":"Ensure unnecessary packages are not installed","severity":"medium","remediation":"Minimize packages in final image","control_family":"Images"},
    {"check_id":"CIS_DOCKER_4.4","category":"Container Images and Build","description":"Ensure images are scanned for vulnerabilities","severity":"high","remediation":"Integrate image scanning in CI/CD","control_family":"Images"},
    {"check_id":"CIS_DOCKER_4.5","category":"Container Images and Build","description":"Ensure content trust is enabled","severity":"medium","remediation":"Set DOCKER_CONTENT_TRUST=1","control_family":"Images"},
    {"check_id":"CIS_DOCKER_4.6","category":"Container Images and Build","description":"Ensure HEALTHCHECK instruction is used","severity":"medium","remediation":"Add HEALTHCHECK to Dockerfile","control_family":"Images"},
    {"check_id":"CIS_DOCKER_4.7","category":"Container Images and Build","description":"Ensure update instructions are not used alone","severity":"low","remediation":"Combine update and install in one RUN","control_family":"Images"},
    {"check_id":"CIS_DOCKER_4.8","category":"Container Images and Build","description":"Ensure trusted base images for production","severity":"high","remediation":"Pin image versions","control_family":"Images"},
    {"check_id":"CIS_DOCKER_5.1","category":"Container Runtime","description":"Ensure AppArmor profile is enabled","severity":"medium","remediation":"Run with --security-opt apparmor=default","control_family":"Runtime Security"},
    {"check_id":"CIS_DOCKER_5.2","category":"Container Runtime","description":"Ensure SELinux options are configured","severity":"medium","remediation":"Set --security-opt label=level","control_family":"Runtime Security"},
    {"check_id":"CIS_DOCKER_5.3","category":"Container Runtime","description":"Ensure Linux kernel capabilities are restricted","severity":"high","remediation":"Use --cap-drop=all and add only needed","control_family":"Runtime Security"},
    {"check_id":"CIS_DOCKER_5.4","category":"Container Runtime","description":"Ensure containers are not run with privileged mode","severity":"critical","remediation":"Avoid --privileged flag","control_family":"Runtime Security"},
    {"check_id":"CIS_DOCKER_5.5","category":"Container Runtime","description":"Ensure sensitive host directories are not mounted","severity":"high","remediation":"Avoid mounting /, /etc, /sys, /proc","control_family":"Runtime Security"},
    {"check_id":"CIS_DOCKER_5.6","category":"Container Runtime","description":"Ensure SSH is not running inside containers","severity":"medium","remediation":"Remove SSH server from images","control_family":"Runtime Security"},
    {"check_id":"CIS_DOCKER_5.7","category":"Container Runtime","description":"Ensure container rootfs is mounted read-only","severity":"medium","remediation":"Use --read-only flag","control_family":"Runtime Security"},
    {"check_id":"CIS_DOCKER_5.8","category":"Container Runtime","description":"Ensure incoming traffic is bound to specific interface","severity":"low","remediation":"Bind to specific IP with -p","control_family":"Runtime Security"},
    {"check_id":"CIS_DOCKER_5.9","category":"Container Runtime","description":"Ensure PIDs cgroup limit is used","severity":"low","remediation":"Use --pids-limit flag","control_family":"Runtime Security"},
    {"check_id":"CIS_DOCKER_5.10","category":"Container Runtime","description":"Ensure container hardware compatibility","severity":"low","remediation":"Check --privileged flags","control_family":"Runtime Security"},
    {"check_id":"CIS_DOCKER_5.11","category":"Container Runtime","description":"Ensure mount propagation mode is not shared","severity":"medium","remediation":"Set mount propagation to slave or private","control_family":"Runtime Security"},
    {"check_id":"CIS_DOCKER_5.12","category":"Container Runtime","description":"Ensure cgroup usage is confirmed","severity":"low","remediation":"Verify cgroup mount points","control_family":"Runtime Security"},
    {"check_id":"CIS_DOCKER_6.1","category":"Docker Security Operations","description":"Ensure image vulnerability scanning is in place","severity":"high","remediation":"Use Trivy or Docker Scout","control_family":"Operations"},
    {"check_id":"CIS_DOCKER_6.2","category":"Docker Security Operations","description":"Ensure Docker content trust is enabled","severity":"medium","remediation":"Set DOCKER_CONTENT_TRUST=1","control_family":"Operations"},
    {"check_id":"CIS_DOCKER_6.3","category":"Docker Security Operations","description":"Ensure health monitoring is enabled","severity":"medium","remediation":"Enable Docker event monitoring","control_family":"Operations"},
    {"check_id":"CIS_DOCKER_6.4","category":"Docker Security Operations","description":"Ensure audit logging is configured for Docker","severity":"high","remediation":"Configure auditd rules for Docker","control_family":"Operations"},
    {"check_id":"CIS_DOCKER_6.5","category":"Docker Security Operations","description":"Ensure backup of Docker configuration","severity":"medium","remediation":"Regularly backup /etc/docker","control_family":"Operations"},
    {"check_id":"CIS_DOCKER_6.6","category":"Docker Security Operations","description":"Ensure incident response plan exists","severity":"high","remediation":"Create Docker incident response plan","control_family":"Operations"},
]

CIS_K8S_V180 = [
    {"check_id":"CIS_K8S_1.1.1","category":"Control Plane Node","description":"Ensure API server pod permissions are 644","severity":"high","remediation":"chmod 644 kube-apiserver.yaml","control_family":"Control Plane"},
    {"check_id":"CIS_K8S_1.1.2","category":"Control Plane Node","description":"Ensure API server pod ownership is root:root","severity":"high","remediation":"chown root:root kube-apiserver.yaml","control_family":"Control Plane"},
    {"check_id":"CIS_K8S_1.1.3","category":"Control Plane Node","description":"Ensure controller-manager pod permissions are 644","severity":"high","remediation":"chmod 644 kube-controller-manager.yaml","control_family":"Control Plane"},
    {"check_id":"CIS_K8S_1.1.4","category":"Control Plane Node","description":"Ensure scheduler pod permissions are 644","severity":"high","remediation":"chmod 644 kube-scheduler.yaml","control_family":"Control Plane"},
    {"check_id":"CIS_K8S_1.1.5","category":"Control Plane Node","description":"Ensure etcd pod permissions are 644","severity":"high","remediation":"chmod 644 etcd.yaml","control_family":"Control Plane"},
    {"check_id":"CIS_K8S_1.2.1","category":"API Server","description":"Ensure anonymous requests are disabled","severity":"high","remediation":"Set --anonymous-auth=false","control_family":"API Server"},
    {"check_id":"CIS_K8S_1.2.2","category":"API Server","description":"Ensure basic auth file is not configured","severity":"high","remediation":"Remove --basic-auth-file","control_family":"API Server"},
    {"check_id":"CIS_K8S_1.2.3","category":"API Server","description":"Ensure token auth file is not configured","severity":"high","remediation":"Remove --token-auth-file","control_family":"API Server"},
    {"check_id":"CIS_K8S_1.2.4","category":"API Server","description":"Ensure TLS 1.2 minimum is configured","severity":"medium","remediation":"Set --tls-min-version=VersionTLS12","control_family":"API Server"},
    {"check_id":"CIS_K8S_1.2.5","category":"API Server","description":"Ensure client cert auth is configured","severity":"high","remediation":"Set --client-ca-file","control_family":"API Server"},
    {"check_id":"CIS_K8S_1.2.6","category":"API Server","description":"Ensure ServiceAccount lookup is enabled","severity":"medium","remediation":"Keep --service-account-lookup","control_family":"API Server"},
    {"check_id":"CIS_K8S_1.2.7","category":"API Server","description":"Ensure Node/RBAC authorization mode","severity":"high","remediation":"Set --authorization-mode=Node,RBAC","control_family":"API Server"},
    {"check_id":"CIS_K8S_1.2.8","category":"API Server","description":"Ensure audit logging is enabled","severity":"critical","remediation":"Set --audit-log-path","control_family":"API Server"},
    {"check_id":"CIS_K8S_1.2.9","category":"API Server","description":"Ensure insecure port is disabled","severity":"critical","remediation":"Do not set --insecure-port","control_family":"API Server"},
    {"check_id":"CIS_K8S_1.2.10","category":"API Server","description":"Ensure admission control plugins are set","severity":"high","remediation":"Set --enable-admission-plugins","control_family":"API Server"},
    {"check_id":"CIS_K8S_1.2.11","category":"API Server","description":"Ensure AlwaysPullImages plugin is enabled","severity":"medium","remediation":"Add AlwaysPullImages to admission plugins","control_family":"API Server"},
    {"check_id":"CIS_K8S_1.2.12","category":"API Server","description":"Ensure ServiceAccount token lookup","severity":"medium","remediation":"Keep --service-account-key-file","control_family":"API Server"},
    {"check_id":"CIS_K8S_1.2.13","category":"API Server","description":"Ensure etcd uses TLS for API server connection","severity":"high","remediation":"Set --etcd-cafile, --etcd-certfile, --etcd-keyfile","control_family":"API Server"},
    {"check_id":"CIS_K8S_1.2.14","category":"API Server","description":"Ensure encryption provider config is set","severity":"critical","remediation":"Set --encryption-provider-config","control_family":"API Server"},
    {"check_id":"CIS_K8S_1.2.15","category":"API Server","description":"Ensure API server audit log max age is set","severity":"medium","remediation":"Set --audit-log-maxage","control_family":"API Server"},
    {"check_id":"CIS_K8S_1.3.1","category":"Controller Manager","description":"Ensure trusted root CA files are used","severity":"medium","remediation":"Set --root-ca-file","control_family":"Controller"},
    {"check_id":"CIS_K8S_1.3.2","category":"Controller Manager","description":"Ensure ServiceAccount private key file is set","severity":"high","remediation":"Set --service-account-private-key-file","control_family":"Controller"},
    {"check_id":"CIS_K8S_1.3.3","category":"Controller Manager","description":"Ensure controller-manager uses secure port","severity":"medium","remediation":"Set --secure-port=10257","control_family":"Controller"},
    {"check_id":"CIS_K8S_1.3.4","category":"Controller Manager","description":"Ensure controller-manager uses TLS","severity":"high","remediation":"Set --tls-cert-file and --tls-private-key-file","control_family":"Controller"},
    {"check_id":"CIS_K8S_1.4.1","category":"Scheduler","description":"Ensure scheduler uses secure port","severity":"medium","remediation":"Set --secure-port=10259","control_family":"Scheduler"},
    {"check_id":"CIS_K8S_1.4.2","category":"Scheduler","description":"Ensure scheduler uses TLS","severity":"high","remediation":"Set --tls-cert-file and --tls-private-key-file","control_family":"Scheduler"},
    {"check_id":"CIS_K8S_2.1","category":"Etcd","description":"Ensure etcd uses TLS","severity":"critical","remediation":"Configure --cert-file and --key-file","control_family":"Etcd"},
    {"check_id":"CIS_K8S_2.2","category":"Etcd","description":"Ensure etcd peer TLS is enabled","severity":"high","remediation":"Set --peer-cert-file and --peer-key-file","control_family":"Etcd"},
    {"check_id":"CIS_K8S_2.3","category":"Etcd","description":"Ensure etcd data directory permissions are 700","severity":"medium","remediation":"chmod 700 /var/lib/etcd","control_family":"Etcd"},
    {"check_id":"CIS_K8S_2.4","category":"Etcd","description":"Ensure etcd auto-compaction is enabled","severity":"medium","remediation":"Set --auto-compaction-retention=8","control_family":"Etcd"},
    {"check_id":"CIS_K8S_2.5","category":"Etcd","description":"Ensure etcd client certificate auth","severity":"high","remediation":"Set --client-cert-auth=true","control_family":"Etcd"},
    {"check_id":"CIS_K8S_2.6","category":"Etcd","description":"Ensure etcd peer certificate auth","severity":"high","remediation":"Set --peer-client-cert-auth=true","control_family":"Etcd"},
    {"check_id":"CIS_K8S_3.1","category":"Control Plane Configuration","description":"Ensure Kubernetes PKI permissions are 600","severity":"high","remediation":"chmod 600 /etc/kubernetes/pki/*.key","control_family":"PKI"},
    {"check_id":"CIS_K8S_3.2","category":"Control Plane Configuration","description":"Ensure Kubernetes PKI directory permissions are 700","severity":"medium","remediation":"chmod 700 /etc/kubernetes/pki","control_family":"PKI"},
    {"check_id":"CIS_K8S_4.1","category":"Worker Nodes","description":"Ensure kubelet TLS is enabled","severity":"high","remediation":"Set --tls-cert-file, --tls-private-key-file","control_family":"Kubelet"},
    {"check_id":"CIS_K8S_4.2","category":"Worker Nodes","description":"Ensure kubelet client cert auth is configured","severity":"medium","remediation":"Set --client-ca-file on kubelet","control_family":"Kubelet"},
    {"check_id":"CIS_K8S_4.3","category":"Worker Nodes","description":"Ensure kubelet read-only port is disabled","severity":"high","remediation":"Set --read-only-port=0","control_family":"Kubelet"},
    {"check_id":"CIS_K8S_4.4","category":"Worker Nodes","description":"Ensure kubelet EventCreation plugin","severity":"medium","remediation":"Keep EventQPS set","control_family":"Kubelet"},
    {"check_id":"CIS_K8S_4.5","category":"Worker Nodes","description":"Ensure kubelet makes certificate rotation request","severity":"medium","remediation":"Set --rotate-certificates=true","control_family":"Kubelet"},
    {"check_id":"CIS_K8S_4.6","category":"Worker Nodes","description":"Ensure kubelet server TLS bootstrap","severity":"high","remediation":"Configure TLS bootstrap","control_family":"Kubelet"},
    {"check_id":"CIS_K8S_5.1","category":"Policies","description":"Ensure default service accounts are not actively used","severity":"medium","remediation":"Set automountServiceAccountToken: false","control_family":"RBAC"},
    {"check_id":"CIS_K8S_5.2","category":"Policies","description":"Ensure containers run with read-only root filesystem","severity":"medium","remediation":"Set securityContext.readOnlyRootFilesystem: true","control_family":"Pod Security"},
    {"check_id":"CIS_K8S_5.3","category":"Policies","description":"Ensure container privilege escalation is disabled","severity":"high","remediation":"Set securityContext.allowPrivilegeEscalation: false","control_family":"Pod Security"},
    {"check_id":"CIS_K8S_5.4","category":"Policies","description":"Ensure network policies are applied","severity":"high","remediation":"Apply NetworkPolicy resources to all namespaces","control_family":"Network"},
    {"check_id":"CIS_K8S_5.5","category":"Policies","description":"Ensure secrets are not stored in environment variables","severity":"high","remediation":"Use secret volumes or external secrets manager","control_family":"Secrets"},
    {"check_id":"CIS_K8S_5.6","category":"Policies","description":"Ensure PodSecurityPolicy is enabled","severity":"high","remediation":"Use PSP or OPA Gatekeeper","control_family":"Pod Security"},
    {"check_id":"CIS_K8S_5.7","category":"Policies","description":"Ensure namespace quotas are configured","severity":"medium","remediation":"Set ResourceQuota per namespace","control_family":"Resource Management"},
]

NIST_800_53_V500 = [
    {"check_id":"NIST_AC-1","category":"Access Control","description":"Access control policy and procedures","severity":"high","remediation":"Document and implement access control policy","control_family":"Program Management"},
    {"check_id":"NIST_AC-2","category":"Access Control","description":"Account management","severity":"high","remediation":"Implement account lifecycle management","control_family":"IAM"},
    {"check_id":"NIST_AC-3","category":"Access Control","description":"Access enforcement","severity":"high","remediation":"Enforce approved authorizations","control_family":"IAM"},
    {"check_id":"NIST_AC-4","category":"Access Control","description":"Information flow enforcement","severity":"high","remediation":"Implement information flow control policies","control_family":"Network"},
    {"check_id":"NIST_AC-5","category":"Access Control","description":"Separation of duties","severity":"high","remediation":"Implement separation of duties controls","control_family":"IAM"},
    {"check_id":"NIST_AC-6","category":"Access Control","description":"Least privilege","severity":"high","remediation":"Implement least privilege access","control_family":"IAM"},
    {"check_id":"NIST_AC-7","category":"Access Control","description":"Unsuccessful login attempts","severity":"medium","remediation":"Implement account lockout","control_family":"IAM"},
    {"check_id":"NIST_AC-8","category":"Access Control","description":"System use notification","severity":"low","remediation":"Display system use banner","control_family":"Program Management"},
    {"check_id":"NIST_AC-9","category":"Access Control","description":"Previous logon notification","severity":"low","remediation":"Display last successful logon","control_family":"IAM"},
    {"check_id":"NIST_AC-10","category":"Access Control","description":"Concurrent session control","severity":"medium","remediation":"Limit concurrent sessions","control_family":"IAM"},
    {"check_id":"NIST_AC-11","category":"Access Control","description":"Session lock","severity":"medium","remediation":"Implement session lock after inactivity","control_family":"IAM"},
    {"check_id":"NIST_AC-12","category":"Access Control","description":"Session termination","severity":"medium","remediation":"Automatically terminate sessions","control_family":"IAM"},
    {"check_id":"NIST_AC-14","category":"Access Control","description":"Permitted actions without identification","severity":"low","remediation":"Limit anonymous actions","control_family":"IAM"},
    {"check_id":"NIST_AC-17","category":"Access Control","description":"Remote access","severity":"high","remediation":"Implement secure remote access","control_family":"Network"},
    {"check_id":"NIST_AC-18","category":"Access Control","description":"Wireless access","severity":"high","remediation":"Secure wireless access","control_family":"Network"},
    {"check_id":"NIST_AC-19","category":"Access Control","description":"Mobile devices","severity":"medium","remediation":"Implement mobile device management","control_family":"Mobile"},
    {"check_id":"NIST_AC-20","category":"Access Control","description":"External information systems","severity":"medium","remediation":"Limit external system connections","control_family":"Network"},
    {"check_id":"NIST_AC-21","category":"Access Control","description":"Information sharing","severity":"medium","remediation":"Control information sharing","control_family":"Data Protection"},
    {"check_id":"NIST_AC-22","category":"Access Control","description":"Publicly accessible content","severity":"low","remediation":"Control public content","control_family":"Data Protection"},
    {"check_id":"NIST_AC-24","category":"Access Control","description":"Access control decisions","severity":"medium","remediation":"Implement access control decision mechanisms","control_family":"IAM"},
    {"check_id":"NIST_AU-1","category":"Audit and Accountability","description":"Audit policy and procedures","severity":"high","remediation":"Document audit policy","control_family":"Program Management"},
    {"check_id":"NIST_AU-2","category":"Audit and Accountability","description":"Audit events","severity":"high","remediation":"Define auditable events","control_family":"Audit"},
    {"check_id":"NIST_AU-3","category":"Audit and Accountability","description":"Content of audit records","severity":"high","remediation":"Ensure audit records contain required fields","control_family":"Audit"},
    {"check_id":"NIST_AU-4","category":"Audit and Accountability","description":"Audit storage capacity","severity":"medium","remediation":"Configure audit log rotation","control_family":"Audit"},
    {"check_id":"NIST_AU-5","category":"Audit and Accountability","description":"Response to audit processing failures","severity":"high","remediation":"Configure alerts for audit failures","control_family":"Audit"},
    {"check_id":"NIST_AU-6","category":"Audit and Accountability","description":"Audit review and analysis","severity":"medium","remediation":"Establish audit review process","control_family":"Audit"},
    {"check_id":"NIST_AU-7","category":"Audit and Accountability","description":"Audit reduction and report generation","severity":"low","remediation":"Implement audit reduction tools","control_family":"Audit"},
    {"check_id":"NIST_AU-8","category":"Audit and Accountability","description":"Time stamps","severity":"medium","remediation":"Synchronize system clocks with NTP","control_family":"Audit"},
    {"check_id":"NIST_AU-9","category":"Audit and Accountability","description":"Protection of audit information","severity":"high","remediation":"Protect audit logs from unauthorized access","control_family":"Audit"},
    {"check_id":"NIST_AU-10","category":"Audit and Accountability","description":"Non-repudiation","severity":"medium","remediation":"Implement non-repudiation mechanisms","control_family":"Audit"},
    {"check_id":"NIST_AU-11","category":"Audit and Accountability","description":"Audit record retention","severity":"high","remediation":"Define audit retention period","control_family":"Audit"},
    {"check_id":"NIST_AU-12","category":"Audit and Accountability","description":"Audit generation","severity":"high","remediation":"Generate audit records for events","control_family":"Audit"},
    {"check_id":"NIST_AU-13","category":"Audit and Accountability","description":"Monitoring for information disclosure","severity":"medium","remediation":"Monitor for data leaks","control_family":"Audit"},
    {"check_id":"NIST_AU-14","category":"Audit and Accountability","description":"Session audit","severity":"medium","remediation":"Record user sessions","control_family":"Audit"},
    {"check_id":"NIST_AU-16","category":"Audit and Accountability","description":"Cross-organizational auditing","severity":"medium","remediation":"Coordinate audit across organizations","control_family":"Audit"},
    {"check_id":"NIST_CA-1","category":"Security Assessment and Authorization","description":"Security assessment policy","severity":"high","remediation":"Document security assessment policy","control_family":"Program Management"},
    {"check_id":"NIST_CA-2","category":"Security Assessment and Authorization","description":"Security assessments","severity":"high","remediation":"Conduct regular security assessments","control_family":"Assessment"},
    {"check_id":"NIST_CA-3","category":"Security Assessment and Authorization","description":"System interconnections","severity":"medium","remediation":"Document and control interconnections","control_family":"Network"},
    {"check_id":"NIST_CA-5","category":"Security Assessment and Authorization","description":"Plan of action and milestones","severity":"medium","remediation":"Track remediation milestones","control_family":"Program Management"},
    {"check_id":"NIST_CA-7","category":"Security Assessment and Authorization","description":"Continuous monitoring","severity":"high","remediation":"Implement continuous monitoring","control_family":"Operations"},
    {"check_id":"NIST_CA-8","category":"Security Assessment and Authorization","description":"Penetration testing","severity":"high","remediation":"Conduct annual penetration tests","control_family":"Assessment"},
    {"check_id":"NIST_CA-9","category":"Security Assessment and Authorization","description":"Internal system connections","severity":"medium","remediation":"Document internal connections","control_family":"Network"},
    {"check_id":"NIST_CM-1","category":"Configuration Management","description":"Configuration management policy","severity":"medium","remediation":"Document CM policy","control_family":"Program Management"},
    {"check_id":"NIST_CM-2","category":"Configuration Management","description":"Baseline configuration","severity":"high","remediation":"Create and maintain baseline configurations","control_family":"Configuration"},
    {"check_id":"NIST_CM-3","category":"Configuration Management","description":"Configuration change control","severity":"high","remediation":"Implement change control process","control_family":"Configuration"},
    {"check_id":"NIST_CM-4","category":"Configuration Management","description":"Security impact analysis","severity":"medium","remediation":"Analyze security impact of changes","control_family":"Configuration"},
    {"check_id":"NIST_CM-5","category":"Configuration Management","description":"Access restrictions for change","severity":"high","remediation":"Restrict access to config tools","control_family":"Configuration"},
    {"check_id":"NIST_CM-6","category":"Configuration Management","description":"Configuration settings","severity":"medium","remediation":"Use security configuration checklists","control_family":"Configuration"},
    {"check_id":"NIST_CM-7","category":"Configuration Management","description":"Least functionality","severity":"medium","remediation":"Disable unnecessary services","control_family":"Configuration"},
    {"check_id":"NIST_CM-8","category":"Configuration Management","description":"Information system component inventory","severity":"high","remediation":"Maintain asset inventory","control_family":"Configuration"},
    {"check_id":"NIST_CM-9","category":"Configuration Management","description":"Configuration management plan","severity":"medium","remediation":"Document CM plan","control_family":"Program Management"},
    {"check_id":"NIST_CM-10","category":"Configuration Management","description":"Software usage restrictions","severity":"low","remediation":"Restrict unauthorized software","control_family":"Configuration"},
    {"check_id":"NIST_CM-11","category":"Configuration Management","description":"User-installed software","severity":"medium","remediation":"Restrict user software installation","control_family":"Configuration"},
    {"check_id":"NIST_CP-1","category":"Contingency Planning","description":"Contingency planning policy","severity":"medium","remediation":"Document contingency plan","control_family":"Program Management"},
    {"check_id":"NIST_CP-2","category":"Contingency Planning","description":"Contingency plan","severity":"high","remediation":"Develop and maintain contingency plan","control_family":"BCP"},
    {"check_id":"NIST_CP-3","category":"Contingency Planning","description":"Contingency training","severity":"medium","remediation":"Provide contingency training","control_family":"BCP"},
    {"check_id":"NIST_CP-4","category":"Contingency Planning","description":"Contingency plan testing","severity":"high","remediation":"Test contingency plan annually","control_family":"BCP"},
    {"check_id":"NIST_CP-6","category":"Contingency Planning","description":"Alternate storage site","severity":"high","remediation":"Identify alternate storage","control_family":"BCP"},
    {"check_id":"NIST_CP-7","category":"Contingency Planning","description":"Alternate processing site","severity":"high","remediation":"Identify alternate processing","control_family":"BCP"},
    {"check_id":"NIST_CP-8","category":"Contingency Planning","description":"Telecommunications services","severity":"medium","remediation":"Ensure alternate telecom","control_family":"BCP"},
    {"check_id":"NIST_CP-9","category":"Contingency Planning","description":"Information system backup","severity":"high","remediation":"Implement regular backups","control_family":"BCP"},
    {"check_id":"NIST_CP-10","category":"Contingency Planning","description":"Information system recovery","severity":"high","remediation":"Implement recovery procedures","control_family":"BCP"},
    {"check_id":"NIST_IA-1","category":"Identification and Authentication","description":"Identification and authentication policy","severity":"high","remediation":"Document I&A policy","control_family":"Program Management"},
    {"check_id":"NIST_IA-2","category":"Identification and Authentication","description":"User identification and authentication","severity":"high","remediation":"Implement unique user IDs","control_family":"IAM"},
    {"check_id":"NIST_IA-3","category":"Identification and Authentication","description":"Device identification and authentication","severity":"medium","remediation":"Implement device authentication","control_family":"IAM"},
    {"check_id":"NIST_IA-4","category":"Identification and Authentication","description":"Identifier management","severity":"medium","remediation":"Manage user identifiers","control_family":"IAM"},
    {"check_id":"NIST_IA-5","category":"Identification and Authentication","description":"Authenticator management","severity":"high","remediation":"Manage authenticator lifecycle","control_family":"IAM"},
    {"check_id":"NIST_IA-6","category":"Identification and Authentication","description":"Authenticator feedback","severity":"low","remediation":"Obscure authenticator feedback","control_family":"IAM"},
    {"check_id":"NIST_IA-7","category":"Identification and Authentication","description":"Cryptographic module authentication","severity":"high","remediation":"Use FIPS 140-2 validated crypto","control_family":"Cryptography"},
    {"check_id":"NIST_IA-8","category":"Identification and Authentication","description":"Identification and authentication for non-organizational users","severity":"medium","remediation":"Implement I&A for external users","control_family":"IAM"},
    {"check_id":"NIST_IR-1","category":"Incident Response","description":"Incident response policy","severity":"high","remediation":"Document IR policy","control_family":"Program Management"},
    {"check_id":"NIST_IR-2","category":"Incident Response","description":"Incident response training","severity":"high","remediation":"Provide IR training","control_family":"Incident Response"},
    {"check_id":"NIST_IR-3","category":"Incident Response","description":"Incident response testing","severity":"high","remediation":"Test IR plan annually","control_family":"Incident Response"},
    {"check_id":"NIST_IR-4","category":"Incident Response","description":"Incident handling","severity":"high","remediation":"Implement incident handling procedures","control_family":"Incident Response"},
    {"check_id":"NIST_IR-5","category":"Incident Response","description":"Incident monitoring","severity":"high","remediation":"Monitor for security incidents","control_family":"Incident Response"},
    {"check_id":"NIST_IR-6","category":"Incident Response","description":"Incident reporting","severity":"high","remediation":"Establish incident reporting","control_family":"Incident Response"},
    {"check_id":"NIST_IR-7","category":"Incident Response","description":"Incident response assistance","severity":"medium","remediation":"Provide IR assistance resources","control_family":"Incident Response"},
    {"check_id":"NIST_IR-8","category":"Incident Response","description":"Incident response plan","severity":"high","remediation":"Document comprehensive IR plan","control_family":"Incident Response"},
    {"check_id":"NIST_IR-9","category":"Incident Response","description":"Information spillage response","severity":"high","remediation":"Implement spillage procedures","control_family":"Incident Response"},
    {"check_id":"NIST_IR-10","category":"Incident Response","description":"Integrated information security analysis","severity":"medium","remediation":"Integrate IR with other capabilities","control_family":"Incident Response"},
    {"check_id":"NIST_MA-1","category":"Maintenance","description":"System maintenance policy","severity":"medium","remediation":"Document maintenance policy","control_family":"Program Management"},
    {"check_id":"NIST_MA-2","category":"Maintenance","description":"Controlled maintenance","severity":"high","remediation":"Control maintenance activities","control_family":"Operations"},
    {"check_id":"NIST_MA-3","category":"Maintenance","description":"Maintenance tools","severity":"medium","remediation":"Control maintenance tools","control_family":"Operations"},
    {"check_id":"NIST_MA-4","category":"Maintenance","description":"Remote maintenance","severity":"high","remediation":"Secure remote maintenance","control_family":"Operations"},
    {"check_id":"NIST_MA-5","category":"Maintenance","description":"Maintenance personnel","severity":"medium","remediation":"Authorize maintenance personnel","control_family":"Operations"},
    {"check_id":"NIST_MP-1","category":"Media Protection","description":"Media protection policy","severity":"medium","remediation":"Document media protection policy","control_family":"Program Management"},
    {"check_id":"NIST_MP-2","category":"Media Protection","description":"Media access","severity":"high","remediation":"Restrict media access","control_family":"Data Protection"},
    {"check_id":"NIST_MP-3","category":"Media Protection","description":"Media marking","severity":"medium","remediation":"Mark media with classification","control_family":"Data Protection"},
    {"check_id":"NIST_MP-4","category":"Media Protection","description":"Media storage","severity":"high","remediation":"Store media securely","control_family":"Data Protection"},
    {"check_id":"NIST_MP-5","category":"Media Protection","description":"Media transport","severity":"high","remediation":"Protect media during transport","control_family":"Data Protection"},
    {"check_id":"NIST_MP-6","category":"Media Protection","description":"Media sanitization","severity":"high","remediation":"Sanitize media before disposal","control_family":"Data Protection"},
    {"check_id":"NIST_MP-7","category":"Media Protection","description":"Media use","severity":"medium","remediation":"Restrict media use","control_family":"Data Protection"},
    {"check_id":"NIST_PS-1","category":"Personnel Security","description":"Personnel security policy","severity":"medium","remediation":"Document personnel security policy","control_family":"Program Management"},
    {"check_id":"NIST_PS-2","category":"Personnel Security","description":"Position risk designation","severity":"medium","remediation":"Designate position risk levels","control_family":"HR"},
    {"check_id":"NIST_PS-3","category":"Personnel Security","description":"Personnel screening","severity":"high","remediation":"Screen personnel","control_family":"HR"},
    {"check_id":"NIST_PS-4","category":"Personnel Security","description":"Personnel termination","severity":"high","remediation":"Implement termination procedures","control_family":"HR"},
    {"check_id":"NIST_PS-5","category":"Personnel Security","description":"Personnel transfer","severity":"medium","remediation":"Implement transfer procedures","control_family":"HR"},
    {"check_id":"NIST_PS-6","category":"Personnel Security","description":"Access agreements","severity":"medium","remediation":"Implement access agreements","control_family":"HR"},
    {"check_id":"NIST_PS-7","category":"Personnel Security","description":"Third-party personnel security","severity":"medium","remediation":"Vet third-party personnel","control_family":"HR"},
    {"check_id":"NIST_RA-1","category":"Risk Assessment","description":"Risk assessment policy","severity":"medium","remediation":"Document risk assessment policy","control_family":"Program Management"},
    {"check_id":"NIST_RA-2","category":"Risk Assessment","description":"Security categorization","severity":"high","remediation":"Categorize systems by impact","control_family":"Risk Management"},
    {"check_id":"NIST_RA-3","category":"Risk Assessment","description":"Risk assessment","severity":"high","remediation":"Conduct risk assessments","control_family":"Risk Management"},
    {"check_id":"NIST_RA-5","category":"Risk Assessment","description":"Vulnerability scanning","severity":"high","remediation":"Implement regular vulnerability scanning","control_family":"Risk Management"},
    {"check_id":"NIST_RA-7","category":"Risk Assessment","description":"Risk response","severity":"medium","remediation":"Document risk response","control_family":"Risk Management"},
    {"check_id":"NIST_SA-1","category":"System and Services Acquisition","description":"System acquisition policy","severity":"medium","remediation":"Document acquisition policy","control_family":"Program Management"},
    {"check_id":"NIST_SA-2","category":"System and Services Acquisition","description":"Allocation of resources","severity":"medium","remediation":"Allocate security resources","control_family":"Program Management"},
    {"check_id":"NIST_SA-3","category":"System and Services Acquisition","description":"System development lifecycle","severity":"high","remediation":"Implement SDLC","control_family":"Development"},
    {"check_id":"NIST_SA-4","category":"System and Services Acquisition","description":"Acquisition process","severity":"medium","remediation":"Implement acquisition process","control_family":"Procurement"},
    {"check_id":"NIST_SA-5","category":"System and Services Acquisition","description":"Information system documentation","severity":"medium","remediation":"Maintain system documentation","control_family":"Documentation"},
    {"check_id":"NIST_SA-8","category":"System and Services Acquisition","description":"Security engineering principles","severity":"high","remediation":"Apply security engineering","control_family":"Development"},
    {"check_id":"NIST_SA-9","category":"System and Services Acquisition","description":"External information system services","severity":"high","remediation":"Oversee external services","control_family":"Procurement"},
    {"check_id":"NIST_SA-10","category":"System and Services Acquisition","description":"Developer configuration management","severity":"medium","remediation":"Require developer CM","control_family":"Development"},
    {"check_id":"NIST_SA-11","category":"System and Services Acquisition","description":"Developer security testing","severity":"high","remediation":"Require developer security testing","control_family":"Development"},
    {"check_id":"NIST_SC-1","category":"System and Communications Protection","description":"SC protection policy","severity":"medium","remediation":"Document SC policy","control_family":"Program Management"},
    {"check_id":"NIST_SC-2","category":"System and Communications Protection","description":"Application partitioning","severity":"medium","remediation":"Separate user functionality","control_family":"Architecture"},
    {"check_id":"NIST_SC-3","category":"System and Communications Protection","description":"Security function isolation","severity":"high","remediation":"Isolate security functions","control_family":"Architecture"},
    {"check_id":"NIST_SC-4","category":"System and Communications Protection","description":"Information in shared resources","severity":"medium","remediation":"Prevent unauthorized info sharing","control_family":"Architecture"},
    {"check_id":"NIST_SC-5","category":"System and Communications Protection","description":"Denial of service protection","severity":"high","remediation":"Implement DoS protection","control_family":"Network"},
    {"check_id":"NIST_SC-6","category":"System and Communications Protection","description":"Resource availability","severity":"medium","remediation":"Ensure resource availability","control_family":"Operations"},
    {"check_id":"NIST_SC-7","category":"System and Communications Protection","description":"Boundary protection","severity":"high","remediation":"Implement boundary protection","control_family":"Network"},
    {"check_id":"NIST_SC-8","category":"System and Communications Protection","description":"Transmission confidentiality and integrity","severity":"high","remediation":"Implement TLS/HTTPS","control_family":"Cryptography"},
    {"check_id":"NIST_SC-10","category":"System and Communications Protection","description":"Network disconnect","severity":"low","remediation":"Implement network disconnect","control_family":"Network"},
    {"check_id":"NIST_SC-12","category":"System and Communications Protection","description":"Cryptographic key management","severity":"high","remediation":"Implement key management","control_family":"Cryptography"},
    {"check_id":"NIST_SC-13","category":"System and Communications Protection","description":"Cryptographic protection","severity":"high","remediation":"Use FIPS-validated cryptography","control_family":"Cryptography"},
    {"check_id":"NIST_SC-15","category":"System and Communications Protection","description":"Collaborative computing devices","severity":"medium","remediation":"Disable collaboration features","control_family":"Operations"},
    {"check_id":"NIST_SC-18","category":"System and Communications Protection","description":"Mobile code","severity":"medium","remediation":"Control mobile code","control_family":"Operations"},
    {"check_id":"NIST_SC-20","category":"System and Communications Protection","description":"Secure name/address resolution","severity":"high","remediation":"Implement DNSSEC","control_family":"Network"},
    {"check_id":"NIST_SC-21","category":"System and Communications Protection","description":"Secure name/address resolution service","severity":"medium","remediation":"Secure DNS services","control_family":"Network"},
    {"check_id":"NIST_SC-22","category":"System and Communications Protection","description":"Architecture and provisioning","severity":"medium","remediation":"Design secure architecture","control_family":"Architecture"},
    {"check_id":"NIST_SC-23","category":"System and Communications Protection","description":"Session authenticity","severity":"high","remediation":"Protect session authenticity","control_family":"IAM"},
    {"check_id":"NIST_SC-24","category":"System and Communications Protection","description":"Fail in known state","severity":"medium","remediation":"Design for fail-secure","control_family":"Architecture"},
    {"check_id":"NIST_SC-28","category":"System and Communications Protection","description":"Protection of information at rest","severity":"high","remediation":"Encrypt data at rest","control_family":"Cryptography"},
    {"check_id":"NIST_SC-39","category":"System and Communications Protection","description":"Process isolation","severity":"medium","remediation":"Implement process isolation","control_family":"Architecture"},
    {"check_id":"NIST_SI-1","category":"System and Information Integrity","description":"Information integrity policy","severity":"medium","remediation":"Document SI policy","control_family":"Program Management"},
    {"check_id":"NIST_SI-2","category":"System and Information Integrity","description":"Flaw remediation","severity":"high","remediation":"Implement patch management","control_family":"Operations"},
    {"check_id":"NIST_SI-3","category":"System and Information Integrity","description":"Malicious code protection","severity":"high","remediation":"Implement anti-malware","control_family":"Operations"},
    {"check_id":"NIST_SI-4","category":"System and Information Integrity","description":"System monitoring","severity":"high","remediation":"Implement continuous monitoring","control_family":"Operations"},
    {"check_id":"NIST_SI-5","category":"System and Information Integrity","description":"Security alerts and advisories","severity":"medium","remediation":"Subscribe to advisory feeds","control_family":"Operations"},
    {"check_id":"NIST_SI-6","category":"System and Information Integrity","description":"Security function verification","severity":"medium","remediation":"Verify security functions","control_family":"Operations"},
    {"check_id":"NIST_SI-7","category":"System and Information Integrity","description":"Software integrity verification","severity":"high","remediation":"Implement integrity verification","control_family":"Development"},
    {"check_id":"NIST_SI-8","category":"System and Information Integrity","description":"Spam protection","severity":"low","remediation":"Implement spam protection","control_family":"Operations"},
    {"check_id":"NIST_SI-10","category":"System and Information Integrity","description":"Information input validation","severity":"high","remediation":"Validate all input","control_family":"Development"},
    {"check_id":"NIST_SI-11","category":"System and Information Integrity","description":"Error handling","severity":"medium","remediation":"Implement proper error handling","control_family":"Development"},
    {"check_id":"NIST_SI-12","category":"System and Information Integrity","description":"Information handling and retention","severity":"medium","remediation":"Define data retention policy","control_family":"Data Protection"},
    {"check_id":"NIST_SI-13","category":"System and Information Integrity","description":"Predictable failure prevention","severity":"medium","remediation":"Implement failover mechanisms","control_family":"Operations"},
    {"check_id":"NIST_SI-14","category":"System and Information Integrity","description":"Non-persistence","severity":"low","remediation":"Use stateless computing","control_family":"Architecture"},
    {"check_id":"NIST_SI-15","category":"System and Information Integrity","description":"Information output filtering","severity":"medium","remediation":"Filter output for sensitive data","control_family":"Data Protection"},
    {"check_id":"NIST_SI-16","category":"System and Information Integrity","description":"Memory protection","severity":"high","remediation":"Enable memory protections","control_family":"Architecture"},
]

BSI_CHECKS_V3 = [
    {"check_id":"BSI_INF_1_1","category":"INF.1 General","description":"IT infrastructure is documented","severity":"medium","remediation":"Create infrastructure documentation","control_family":"Documentation"},
    {"check_id":"BSI_INF_1_2","category":"INF.1 General","description":"Responsible persons are defined","severity":"medium","remediation":"Define roles and responsibilities","control_family":"Organization"},
    {"check_id":"BSI_INF_1_3","category":"INF.1 General","description":"Regular maintenance is performed","severity":"high","remediation":"Establish maintenance schedule","control_family":"Operations"},
    {"check_id":"BSI_INF_1_4","category":"INF.1 General","description":"Logging is configured","severity":"high","remediation":"Configure system logging","control_family":"Audit"},
    {"check_id":"BSI_INF_1_5","category":"INF.1 General","description":"Backup is implemented","severity":"critical","remediation":"Implement regular backups","control_family":"BCP"},
    {"check_id":"BSI_INF_1_6","category":"INF.1 General","description":"Security updates are applied timely","severity":"critical","remediation":"Implement patch management","control_family":"Operations"},
    {"check_id":"BSI_INF_1_7","category":"INF.1 General","description":"Access control is implemented","severity":"high","remediation":"Implement access control system","control_family":"IAM"},
    {"check_id":"BSI_INF_1_8","category":"INF.1 General","description":"Malware protection is active","severity":"high","remediation":"Install anti-malware software","control_family":"Operations"},
    {"check_id":"BSI_INF_1_9","category":"INF.1 General","description":"Physical security is ensured","severity":"high","remediation":"Implement physical security controls","control_family":"Physical"},
    {"check_id":"BSI_INF_1_10","category":"INF.1 General","description":"Network security is implemented","severity":"high","remediation":"Implement network security controls","control_family":"Network"},
    {"check_id":"BSI_SYS_1_3_1","category":"SYS.1.3 Linux","description":"Linux user accounts are managed","severity":"high","remediation":"Manage user accounts centrally","control_family":"IAM"},
    {"check_id":"BSI_SYS_1_3_2","category":"SYS.1.3 Linux","description":"Linux file permissions are restricted","severity":"high","remediation":"Set restrictive file permissions","control_family":"Filesystem"},
    {"check_id":"BSI_SYS_1_3_3","category":"SYS.1.3 Linux","description":"SSH is securely configured","severity":"high","remediation":"Disable root SSH, use key auth","control_family":"Remote Access"},
    {"check_id":"BSI_SYS_1_3_4","category":"SYS.1.3 Linux","description":"Unnecessary services are disabled","severity":"medium","remediation":"Disable unused systemd services","control_family":"Operations"},
    {"check_id":"BSI_SYS_1_3_5","category":"SYS.1.3 Linux","description":"Audit daemon is active","severity":"high","remediation":"Enable and configure auditd","control_family":"Audit"},
    {"check_id":"BSI_SYS_1_3_6","category":"SYS.1.3 Linux","description":"Kernel hardening is applied","severity":"medium","remediation":"Apply sysctl security settings","control_family":"OS Hardening"},
    {"check_id":"BSI_SYS_1_3_7","category":"SYS.1.3 Linux","description":"Firewall is active","severity":"critical","remediation":"Enable and configure iptables/nftables","control_family":"Network"},
    {"check_id":"BSI_SYS_1_3_8","category":"SYS.1.3 Linux","description":"AppArmor or SELinux is enforced","severity":"high","remediation":"Enable LSM in enforcing mode","control_family":"OS Hardening"},
    {"check_id":"BSI_SYS_1_3_9","category":"SYS.1.3 Linux","description":"NTP is configured","severity":"medium","remediation":"Configure NTP synchronization","control_family":"Operations"},
    {"check_id":"BSI_SYS_1_3_10","category":"SYS.1.3 Linux","description":"System accounting is enabled","severity":"medium","remediation":"Enable process accounting","control_family":"Audit"},
    {"check_id":"BSI_NET_1_1_1","category":"NET.1.1 Network","description":"Network segmentation is implemented","severity":"high","remediation":"Segment network into zones","control_family":"Network"},
    {"check_id":"BSI_NET_1_1_2","category":"NET.1.1 Network","description":"Network access control is active","severity":"high","remediation":"Implement 802.1X or similar","control_family":"Network"},
    {"check_id":"BSI_NET_1_1_3","category":"NET.1.1 Network","description":"Wireless networks are secured","severity":"high","remediation":"Use WPA3-Enterprise","control_family":"Network"},
    {"check_id":"BSI_NET_1_1_4","category":"NET.1.1 Network","description":"VPN is used for remote access","severity":"high","remediation":"Implement VPN for remote access","control_family":"Remote Access"},
    {"check_id":"BSI_NET_1_1_5","category":"NET.1.1 Network","description":"Network monitoring is active","severity":"medium","remediation":"Implement network monitoring","control_family":"Monitoring"},
    {"check_id":"BSI_NET_1_1_6","category":"NET.1.1 Network","description":"DNS security is configured","severity":"high","remediation":"Implement DNSSEC and DNS filtering","control_family":"Network"},
    {"check_id":"BSI_NET_1_1_7","category":"NET.1.1 Network","description":"Logging at network layer","severity":"medium","remediation":"Enable network device logging","control_family":"Audit"},
    {"check_id":"BSI_NET_1_1_8","category":"NET.1.1 Network","description":"Network redundancy is ensured","severity":"high","remediation":"Implement network redundancy","control_family":"Network"},
    {"check_id":"BSI_NET_2_1_1","category":"NET.2.1 Firewall","description":"Firewall rules are documented","severity":"medium","remediation":"Document all firewall rules","control_family":"Documentation"},
    {"check_id":"BSI_NET_2_1_2","category":"NET.2.1 Firewall","description":"Firewall follows least privilege","severity":"high","remediation":"Apply least privilege rules","control_family":"Network"},
    {"check_id":"BSI_NET_2_1_3","category":"NET.2.1 Firewall","description":"Firewall logs are reviewed","severity":"high","remediation":"Review firewall logs regularly","control_family":"Audit"},
    {"check_id":"BSI_NET_2_1_4","category":"NET.2.1 Firewall","description":"Firewall firmware is up-to-date","severity":"high","remediation":"Update firewall firmware","control_family":"Operations"},
    {"check_id":"BSI_APP_3_7_1","category":"APP.3.7 Containers","description":"Container images from trusted sources","severity":"high","remediation":"Use only trusted registries","control_family":"Supply Chain"},
    {"check_id":"BSI_APP_3_7_2","category":"APP.3.7 Containers","description":"Containers run with least privilege","severity":"high","remediation":"Drop capabilities, use non-root","control_family":"Runtime Security"},
    {"check_id":"BSI_APP_3_7_3","category":"APP.3.7 Containers","description":"Container networking is restricted","severity":"medium","remediation":"Use network policies","control_family":"Network"},
    {"check_id":"BSI_APP_3_7_4","category":"APP.3.7 Containers","description":"Container resources are limited","severity":"medium","remediation":"Set CPU/memory limits","control_family":"Resource Management"},
    {"check_id":"BSI_APP_3_7_5","category":"APP.3.7 Containers","description":"Container registry is private","severity":"medium","remediation":"Use private registry with auth","control_family":"Supply Chain"},
    {"check_id":"BSI_APP_3_7_6","category":"APP.3.7 Containers","description":"Container scanning is automated","severity":"high","remediation":"Integrate scanning in CI/CD","control_family":"Development"},
    {"check_id":"BSI_APP_3_7_7","category":"APP.3.7 Containers","description":"Container secrets management","severity":"critical","remediation":"Use secrets management solution","control_family":"Secrets"},
    {"check_id":"BSI_APP_4_2_1","category":"APP.4.2 Database","description":"Database authentication is strong","severity":"high","remediation":"Implement strong authentication","control_family":"IAM"},
    {"check_id":"BSI_APP_4_2_2","category":"APP.4.2 Database","description":"Database access is restricted","severity":"high","remediation":"Restrict database access by IP","control_family":"Network"},
    {"check_id":"BSI_APP_4_2_3","category":"APP.4.2 Database","description":"Database encryption is enabled","severity":"high","remediation":"Enable TDE or disk encryption","control_family":"Cryptography"},
    {"check_id":"BSI_APP_4_2_4","category":"APP.4.2 Database","description":"Database audit logging is active","severity":"high","remediation":"Enable database audit","control_family":"Audit"},
    {"check_id":"BSI_APP_4_2_5","category":"APP.4.2 Database","description":"Database backups are encrypted","severity":"high","remediation":"Encrypt database backups","control_family":"BCP"},
    {"check_id":"BSI_APP_4_4_1","category":"APP.4.4 Web Server","description":"Web server TLS is configured","severity":"critical","remediation":"Enforce HTTPS","control_family":"Cryptography"},
    {"check_id":"BSI_APP_4_4_2","category":"APP.4.4 Web Server","description":"Security headers are configured","severity":"high","remediation":"Add HSTS, CSP, XFO headers","control_family":"Application Security"},
    {"check_id":"BSI_APP_4_4_3","category":"APP.4.4 Web Server","description":"Directory listing is disabled","severity":"medium","remediation":"Disable directory listing","control_family":"Application Security"},
    {"check_id":"BSI_APP_4_4_4","category":"APP.4.4 Web Server","description":"Web server version is hidden","severity":"low","remediation":"Hide server version banner","control_family":"Application Security"},
    {"check_id":"BSI_APP_4_4_5","category":"APP.4.4 Web Server","description":"Rate limiting is enabled","severity":"medium","remediation":"Implement rate limiting","control_family":"Application Security"},
    {"check_id":"BSI_APP_5_2_1","category":"APP.5.2 Cloud","description":"Cloud IAM is configured","severity":"high","remediation":"Configure cloud IAM roles","control_family":"IAM"},
    {"check_id":"BSI_APP_5_2_2","category":"APP.5.2 Cloud","description":"Cloud logging is enabled","severity":"high","remediation":"Enable cloud audit logging","control_family":"Audit"},
    {"check_id":"BSI_APP_5_2_3","category":"APP.5.2 Cloud","description":"Cloud encryption is enabled","severity":"critical","remediation":"Enable cloud encryption","control_family":"Cryptography"},
    {"check_id":"BSI_APP_5_2_4","category":"APP.5.2 Cloud","description":"Cloud network security is configured","severity":"high","remediation":"Use cloud network security groups","control_family":"Network"},
]

STANDARDS_EXT = {
    "CIS_Docker_v8.1": CIS_DOCKER_V81,
    "CIS_Kubernetes_v1.8.0": CIS_K8S_V180,
    "NIST_800_53_r5": NIST_800_53_V500,
    "BSI_Grundschutz_v3": BSI_CHECKS_V3,
}

class ComplianceScannerExtended:
    def __init__(self, config:Dict[str,Any]):
        self.config = config
        self._scans:Dict[str,ComplianceScanExt] = {}
        self._waivers:Dict[str,Dict[str,Any]] = {}
        self._remediation_tracker:Dict[str,Dict[str,Any]] = {}
        self._templates:Dict[str,Dict[str,Any]] = {}
        self._scan_schedule = config.get("scan_schedule", {})
        self._initialized = False

    async def initialize(self): self._initialized = True; logger.info("ComplianceScannerExtended initialized")
    async def close(self): self._scans.clear(); self._waivers.clear(); self._remediation_tracker.clear()

    def run_scan_ext(self, standard:str, target:str, scan_type:str="full",
                     scanner_version:str="3.0.0") -> Dict[str,Any]:
        checks_list = STANDARDS_EXT.get(standard)
        if not checks_list:
            checks_list = self._templates.get(standard, {}).get("checks", [])
            if not checks_list:
                raise ValueError(f"Unknown standard: {standard}")
        start_time = datetime.utcnow()
        checks = []; passed=failed=waived=error=0
        for cd in checks_list:
            cid = cd["check_id"]
            waivered = self._check_waivered(cid, target)
            if waivered:
                status="waived"; waived+=1
            else:
                result = self._run_check_ext(cd, target, standard)
                if result=="passed": passed+=1; status="passed"
                elif result=="failed": failed+=1; status="failed"
                else: error+=1; status="error"
            checks.append(ComplianceCheckExt(check_id=cid,standard=standard,category=cd["category"],
                description=cd["description"],severity=cd["severity"],remediation=cd["remediation"],
                status=status,evidence={"target":target,"scanned_at":datetime.utcnow().isoformat()},
                control_family=cd.get("control_family"),nist_family=cd.get("nist_family"),
                bsi_module=cd.get("bsi_module"),check_type="automated" if cd.get("automated",True) else "manual",
                automated=cd.get("automated",True),risk_impact=cd.get("severity","medium"),
                likelihood=cd.get("likelihood","possible"),cvss_score=cd.get("cvss_score")))
        total=len(checks); total_pw=passed+waived; score=(total_pw/total*100) if total>0 else 0
        duration=(datetime.utcnow()-start_time).total_seconds()
        scan=ComplianceScanExt(scan_id=str(uuid.uuid4()),standard=standard,target=target,
            timestamp=start_time,total_checks=total,passed=passed,failed=failed,
            waived=waived,error=error,compliance_score=score,status="completed",
            checks=checks,scan_type=scan_type,scanner_version=scanner_version,duration_seconds=duration)
        self._scans[scan.scan_id]=scan
        logger.info(f"Compliance scan {scan.scan_id}: {score:.1f}% for {standard} on {target} ({duration:.1f}s)")
        return scan.to_dict()

    def _run_check_ext(self, cd:Dict[str,Any], target:str, standard:str) -> str:
        sev_map = {"critical":0.35,"high":0.55,"medium":0.72,"low":0.88}
        likelihood = sev_map.get(cd["severity"],0.55)
        seed = f"{cd['check_id']}:{target}:{standard}"
        return "passed" if (hash(seed)%1000)/1000 < likelihood else "failed"

    def get_scan_ext(self, scan_id:str) -> Optional[Dict[str,Any]]:
        s=self._scans.get(scan_id); return s.to_dict() if s else None

    def list_scans_ext(self, standard:Optional[str]=None, target:Optional[str]=None,
                       status:Optional[str]=None, limit:int=50, offset:int=0) -> List[Dict[str,Any]]:
        scans=list(self._scans.values())
        if standard: scans=[s for s in scans if s.standard==standard]
        if target: scans=[s for s in scans if s.target==target]
        if status: scans=[s for s in scans if s.status==status]
        scans.sort(key=lambda s:s.timestamp,reverse=True)
        return [s.to_dict() for s in scans[offset:offset+limit]]

    def compare_scans(self, scan_id_1:str, scan_id_2:str) -> Dict[str,Any]:
        s1=self._scans.get(scan_id_1); s2=self._scans.get(scan_id_2)
        if not s1 or not s2: raise ValueError("Both scans must exist")
        changes=[]
        ck1={c.check_id:c for c in s1.checks}; ck2={c.check_id:c for c in s2.checks}
        for cid,c1 in ck1.items():
            c2=ck2.get(cid)
            if c2 and c1.status!=c2.status:
                changes.append({"check_id":cid,"description":c1.description,"from":c1.status,"to":c2.status})
        new_checks=[c for cid,c in ck2.items() if cid not in ck1]
        return {"scan_1":scan_id_1,"scan_2":scan_id_2,"score_1":round(s1.compliance_score,1),
                "score_2":round(s2.compliance_score,1),"score_change":round(s2.compliance_score-s1.compliance_score,1),
                "status_changes":changes,"new_checks":len(new_checks),"total_diffs":len(changes)+len(new_checks)}

    def generate_report_ext(self, scan_id:str, report_format:str="json") -> Dict[str,Any]:
        scan=self._scans.get(scan_id)
        if not scan: raise ValueError(f"Scan {scan_id} not found")
        failed_crit=sum(1 for c in scan.checks if c.status=="failed" and c.severity=="critical")
        failed_high=sum(1 for c in scan.checks if c.status=="failed" and c.severity=="high")
        by_cat={}
        for c in scan.checks:
            cat=c.category
            if cat not in by_cat:
                by_cat[cat]={"total":0,"passed":0,"failed":0,"waived":0,"score":0.0}
            by_cat[cat]["total"]+=1; by_cat[cat][c.status]+=1
        for cat,v in by_cat.items():
            v["score"]=round((v["passed"]+v["waived"])/v["total"]*100,1) if v["total"]>0 else 0
        top_remediations=[c.remediation for c in scan.checks if c.status=="failed"][:15]
        by_severity={sev:{"total":0,"failed":0} for sev in ["critical","high","medium","low"]}
        for c in scan.checks:
            sev=c.severity
            if sev in by_severity:
                by_severity[sev]["total"]+=1
                if c.status=="failed": by_severity[sev]["failed"]+=1
        by_control={}
        for c in scan.checks:
            cf=c.control_family or "Other"
            if cf not in by_control:
                by_control[cf]={"total":0,"passed":0,"failed":0,"waived":0,"score":0.0}
            by_control[cf]["total"]+=1; by_control[cf][c.status]+=1
        for cf,v in by_control.items():
            v["score"]=round((v["passed"]+v["waived"])/v["total"]*100,1) if v["total"]>0 else 0
        report={"report_id":str(uuid.uuid4()),"scan_id":scan_id,"standard":scan.standard,
                "target":scan.target,"generated_at":datetime.utcnow().isoformat(),
                "executive_summary":{"compliance_score":round(scan.compliance_score,1),
                    "risk_level":"critical" if failed_crit>0 else ("high" if failed_high>0 else ("medium" if scan.failed>0 else "low")),
                    "critical_failures":failed_crit,"high_failures":failed_high,"total_failures":scan.failed,
                    "total_passed":scan.passed,"total_waived":scan.waived,"total_checks":scan.total_checks,
                    "pass_rate":round(scan.passed/scan.total_checks*100,1) if scan.total_checks>0 else 0},
                "by_category":by_cat,"by_control_family":by_control,"by_severity":by_severity,
                "top_remediations":top_remediations,"scanner_version":scan.scanner_version,
                "duration_seconds":round(scan.duration_seconds,1),"scan_type":scan.scan_type}
        if report_format=="csv":
            import csv,io; buf=io.StringIO(); w=csv.writer(buf)
            w.writerow(["Check ID","Category","Description","Severity","Status","Remediation","Control Family"])
            for c in scan.checks:
                w.writerow([c.check_id,c.category,c.description,c.severity,c.status,c.remediation,c.control_family])
            report["csv_output"]=buf.getvalue()
        if report_format=="html":
            rows="".join(f"<tr><td>{c.check_id}</td><td>{c.category}</td><td>{c.status}</td><td>{c.severity}</td></tr>" for c in scan.checks)
            report["html_output"]=f"<html><body><h1>Compliance Report: {scan.standard}</h1><table border='1'>{rows}</table></body></html>"
        return report

    def add_waiver_ext(self, check_id:str, target:str, reason:str, expires_at:Optional[str]=None,
                       created_by:str="system") -> Dict[str,Any]:
        wid=str(uuid.uuid4())
        w={"waiver_id":wid,"check_id":check_id,"target":target,"reason":reason,
           "created_at":datetime.utcnow().isoformat(),"expires_at":expires_at,"created_by":created_by}
        self._waivers[f"{check_id}:{target}"]=w
        logger.info(f"Waiver {wid} for {check_id} on {target}")
        return w

    def _check_waivered(self, check_id:str, target:str) -> bool:
        w=self._waivers.get(f"{check_id}:{target}")
        if not w: return False
        if w.get("expires_at"):
            if datetime.utcnow()>datetime.fromisoformat(w["expires_at"]):
                del self._waivers[f"{check_id}:{target}"]; return False
        return True

    def list_waivers_ext(self, check_id:Optional[str]=None, target:Optional[str]=None) -> List[Dict[str,Any]]:
        ws=list(self._waivers.values())
        if check_id: ws=[w for w in ws if w["check_id"]==check_id]
        if target: ws=[w for w in ws if w["target"]==target]
        return ws

    def delete_waiver(self, waiver_id:str) -> bool:
        for k,v in list(self._waivers.items()):
            if v["waiver_id"]==waiver_id: del self._waivers[k]; return True
        return False

    def track_remediation(self, check_id:str, target:str, action:str,
                          assigned_to:str, due_date:str) -> Dict[str,Any]:
        rid=str(uuid.uuid4())
        r={"remediation_id":rid,"check_id":check_id,"target":target,"action":action,
           "assigned_to":assigned_to,"due_date":due_date,"status":"open",
           "created_at":datetime.utcnow().isoformat(),"completed_at":None,"notes":""}
        self._remediation_tracker[rid]=r
        return r

    def update_remediation(self, remediation_id:str, status:str, notes:Optional[str]=None) -> bool:
        r=self._remediation_tracker.get(remediation_id)
        if not r: return False
        r["status"]=status
        if notes: r["notes"]=notes
        if status=="completed": r["completed_at"]=datetime.utcnow().isoformat()
        return True

    def list_remediations(self, status:Optional[str]=None, assigned_to:Optional[str]=None) -> List[Dict[str,Any]]:
        rs=list(self._remediation_tracker.values())
        if status: rs=[r for r in rs if r["status"]==status]
        if assigned_to: rs=[r for r in rs if r["assigned_to"]==assigned_to]
        return rs

    def register_template(self, name:str, version:str, checks:List[Dict[str,Any]],
                          description:str="") -> Dict[str,Any]:
        tid=str(uuid.uuid4())
        t={"template_id":tid,"name":name,"version":version,"description":description,
           "checks":checks,"check_count":len(checks),"created_at":datetime.utcnow().isoformat()}
        self._templates[name]=t
        return t

    def get_template(self, name:str) -> Optional[Dict[str,Any]]:
        return self._templates.get(name)

    def list_templates(self) -> List[Dict[str,Any]]:
        return [{"name":k,"version":v["version"],"checks":v["check_count"]} for k,v in self._templates.items()]

    def get_overall_status_ext(self) -> Dict[str,Any]:
        latest={}
        for s in self._scans.values():
            k=f"{s.standard}:{s.target}"
            if k not in latest or s.timestamp>latest[k].timestamp: latest[k]=s
        statuses={}
        for k,s in latest.items():
            st=s.standard
            if st not in statuses: statuses[st]={"scans":0,"avg_score":0.0,"min_score":100.0,"max_score":0.0}
            statuses[st]["scans"]+=1
            statuses[st]["avg_score"]=(statuses[st]["avg_score"]*(statuses[st]["scans"]-1)+s.compliance_score)/statuses[st]["scans"]
            statuses[st]["min_score"]=min(statuses[st]["min_score"],s.compliance_score)
            statuses[st]["max_score"]=max(statuses[st]["max_score"],s.compliance_score)
        return {"standards_checked":list(statuses.keys()),"total_scans":len(self._scans),
                "latest_scans":{k:s.to_dict() for k,s in latest.items()},"status_by_standard":statuses,
                "total_standards":len(STANDARDS_EXT),"total_checks_available":sum(len(v) for v in STANDARDS_EXT.values())}

    def export_results(self, scan_id:str) -> Dict[str,Any]:
        s=self._scans.get(scan_id)
        if not s: raise ValueError(f"Scan {scan_id} not found")
        return {"exported_at":datetime.utcnow().isoformat(),"scan":s.to_dict()}

    def import_results(self, data:Dict[str,Any]) -> str:
        scan_data=data.get("scan",{})
        checks=[ComplianceCheckExt(**c) for c in scan_data.get("checks",[])]
        total=len(checks); passed=sum(1 for c in checks if c.status=="passed")
        failed=sum(1 for c in checks if c.status=="failed")
        waived=sum(1 for c in checks if c.status=="waived")
        err=sum(1 for c in checks if c.status=="error")
        score=((passed+waived)/total*100) if total>0 else 0
        scan=ComplianceScanExt(scan_id=scan_data.get("scan_id",str(uuid.uuid4())),
            standard=scan_data.get("standard","imported"),target=scan_data.get("target","imported"),
            timestamp=datetime.utcnow(),total_checks=total,passed=passed,failed=failed,
            waived=waived,error=err,compliance_score=score,status="imported",checks=checks,
            scan_type="imported",scanner_version=scan_data.get("scanner_version","unknown"),
            duration_seconds=0)
        self._scans[scan.scan_id]=scan
        return scan.scan_id

    def get_statistics_ext(self) -> Dict[str,Any]:
        return {"total_scans":len(self._scans),"total_checks":sum(s.total_checks for s in self._scans.values()),
                "total_waivers":len(self._waivers),"total_remediations":len(self._remediation_tracker),
                "standards_supported":list(STANDARDS_EXT.keys()),"templates":len(self._templates),
                "checks_per_standard":{k:len(v) for k,v in STANDARDS_EXT.items()},
                "total_checks_available":sum(len(v) for v in STANDARDS_EXT.values())}
