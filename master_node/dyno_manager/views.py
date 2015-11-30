import json
import http.client

from core.models import SystemAudit, Cluster
from django.http import HttpResponse
from django.views.decorators.csrf import csrf_exempt


@csrf_exempt
def systemstatus(request):
    body_unicode = request.body.decode('utf-8')
    stat = json.loads(body_unicode)
    auditEntry = SystemAudit(disk_usage=stat['disk_usage'],
                             memory_usage=stat['memory_usage'],
                             cpu_usage=stat['cpu_usage'],
                             network_usage=stat['network_usage'],
                             )
    auditEntry.cluster_id = stat['cluster']
    auditEntry.save()
    data = json.dumps({'cluster_id': stat['cluster']})
    params = json.dumps({"topic": "Dyno_Manager", "data": data, "priority": 3})
    headers = {"Content-type": "application/x-www-form-urlencoded", "Accept": "text/plain"}
    conn = http.client.HTTPConnection("localhost:4242")
    conn.request("POST", "/queue/enqueue", params, headers)
    response = conn.getresponse()
    data = response.read()
    conn.close()

    return HttpResponse(stat.__str__())


@csrf_exempt
def registerCluster(request):
    body_unicode = request.body.decode('utf-8')
    clusterData = json.loads(body_unicode)
    cluster = Cluster()
    cluster.ip = clusterData['ip']
    cluster.location = clusterData['location']
    cluster.type = clusterData['type']
    cluster.status = 'active'
    cluster.save()

    reply = {}
    reply['ip'] = cluster.ip
    reply['location'] = cluster.location
    reply['type'] = cluster.type
    reply['id'] = cluster.id
    reply['boot_time'] = str(cluster.last_boot_time)
    return HttpResponse(json.dumps(reply))


def getStats(request):
    reply = {}
    clusters = Cluster.objects.filter(status='active')
    for cluster in clusters:
        body_unicode = request.body.decode('utf-8')
        stats = SystemAudit.objects.filter(cluster_id=cluster.id).order_by('time').reverse()[:30]
        i = 0
        cpu_data = []
        for stat in reversed(stats):
            i = i + 1
            cpu_data.append([i, stat.cpu_usage])
        reply['memory'] = stats[0].memory_usage
        reply['disk'] = stats[0].disk_usage
        reply['network'] = stats[0].network_usage
        reply['cpu'] = cpu_data
    return HttpResponse(json.dumps(reply))
