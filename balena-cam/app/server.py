import asyncio, json, os, cv2, platform, sys, io
from websocket import create_connection
import base64
import json
import logging
from time import sleep
from aiohttp import web
import aiohttp
from av import VideoFrame
from aiortc import RTCPeerConnection, RTCSessionDescription, VideoStreamTrack, RTCIceServer, RTCConfiguration, MediaStreamTrack
from aiortc.contrib.media import MediaBlackhole, MediaPlayer, MediaRecorder
from aiortc.mediastreams import MediaStreamError
from aiohttp_basicauth import BasicAuthMiddleware
from imageio import imread
from formencode import variabledecode
import time
from PIL import Image
import numpy

os.environ['isLoggedIn'] = "False"
os.environ['currTime'] = str(time.time())

class CameraDevice():
    def __init__(self):
        self.cap = cv2.VideoCapture(0)
        ret, frame = self.cap.read()
        if not ret:
            print('Failed to open default camera. Exiting...')
            sys.exit()
        self.cap.set(3, 720)
        self.cap.set(4, 720)

    def rotate(self, frame):
        if flip:
            (h, w) = frame.shape[:2]
            center = (w/2, h/2)
            M = cv2.getRotationMatrix2D(center, 180, 1.0)
            frame = cv2.warpAffine(frame, M, (w, h))
        return frame
    # resize and save frame as base64 for classification

    def base64_img(self, frame):
        encode_param = (int(cv2.IMWRITE_JPEG_QUALITY), 90)
        global jpg_base64
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        face_cascade = cv2.CascadeClassifier('haarcascade_frontalface_alt2.xml')
        faces = face_cascade.detectMultiScale(gray,1.1,4)
        for (x, y, w, h) in faces:
            # logging.warning(w,h)
            # cv2.rectangle(frame, (x, y), (x+w, y+h), (0, 0, 255), 2)
            if h >= 160 and w >= 160:
                # print("height > 160 and width too")
                faces = frame[y:y+h,x:x+w]
                jpg_base64 = cv2.resize(faces, (160, 160), interpolation = cv2.INTER_AREA)
                _frame, jpg_base64 = cv2.imencode('.jpg', jpg_base64, encode_param)
                jpg_base64 = base64.b64encode(jpg_base64)
                # logging.warning(jpg_base64)
            else:
                faces = frame
                jpg_base64 = cv2.resize(frame, (160, 160), interpolation = cv2.INTER_AREA)
                _frame, jpg_base64 = cv2.imencode('.jpg', jpg_base64, encode_param)
                jpg_base64 = base64.b64encode(jpg_base64)
        # print(jpg_base64)

    async def get_latest_frame(self):
        ret, frame = self.cap.read()
        await asyncio.sleep(0)
        frame = self.rotate(frame)

        self.base64_img(frame)

        return frame

    async def get_jpeg_frame(self):
        ret, frame = self.cap.read()
        await asyncio.sleep(0)
        frame = self.rotate(frame)

        self.base64_img(frame)

        encode_param = (int(cv2.IMWRITE_JPEG_QUALITY), 90)
        frame, encimg = cv2.imencode('.jpg', frame, encode_param)

        return encimg.tostring()

class PeerConnectionFactory():
    def __init__(self):
        self.config = {'sdpSemantics': 'unified-plan'}
        self.STUN_SERVER = "stun:stun.l.google.com:19302"
        self.TURN_SERVER = None
        self.TURN_USERNAME = None
        self.TURN_PASSWORD = None
        if all(k in os.environ for k in ('STUN_SERVER', 'TURN_SERVER', 'TURN_USERNAME', 'TURN_PASSWORD')):
            print('WebRTC connections will use your custom ICE Servers (STUN / TURN).')
            self.STUN_SERVER = os.environ['STUN_SERVER']
            self.TURN_SERVER = os.environ['TURN_SERVER']
            self.TURN_USERNAME = os.environ['TURN_USERNAME']
            self.TURN_PASSWORD = os.environ['TURN_PASSWORD']
        iceServers = [
            {
                'urls': self.STUN_SERVER
            },
            {
                'urls': self.TURN_SERVER,
                'credential': self.TURN_PASSWORD,
                'username': self.TURN_USERNAME
            }
                    ]
        self.config['iceServers'] = iceServers if self.TURN_SERVER != None else []
        # self.TURN_SERVER = None

    def create_peer_connection(self):
        if self.TURN_SERVER is not None:
            iceServers = []
            iceServers.append(RTCIceServer(self.STUN_SERVER))
            iceServers.append(RTCIceServer(self.TURN_SERVER, username=self.TURN_USERNAME, credential=self.TURN_PASSWORD))
            return RTCPeerConnection(RTCConfiguration(iceServers))
        return RTCPeerConnection()

    def get_ice_config(self):
        return json.dumps(self.config)


class RTCVideoStream(VideoStreamTrack):
    def __init__(self, camera_device):
        super().__init__()
        self.camera_device = camera_device
        self.data_bgr = None

    async def recv(self):
        self.data_bgr = await self.camera_device.get_latest_frame()
        frame = VideoFrame.from_ndarray(self.data_bgr, format='bgr24')
        pts, time_base = await self.next_timestamp()
        frame.pts = pts
        frame.time_base = time_base
        return frame

async def index(request):
    content = open(os.path.join(ROOT, 'client/index.html'), 'r').read()
    return web.Response(content_type='text/html', text=content)

async def stylesheet(request):
    content = open(os.path.join(ROOT, 'client/style.css'), 'r').read()
    return web.Response(content_type='text/css', text=content)

async def javascript(request):
    content = open(os.path.join(ROOT, 'client/client.js'), 'r').read()
    return web.Response(content_type='application/javascript', text=content)

async def balena(request):
    content = open(os.path.join(ROOT, 'client/balena-cam.svg'), 'r').read()
    return web.Response(content_type='image/svg+xml', text=content)

async def balena_logo(request):
    content = open(os.path.join(ROOT, 'client/balena-logo.svg'), 'r').read()
    return web.Response(content_type='image/svg+xml', text=content)

async def edgeimpulse_logo(request):
    content = open(os.path.join(ROOT, 'client/edgeimpulse-logo-white.svg'), 'r').read()
    return web.Response(content_type='image/svg+xml', text=content)

async def favicon(request):
    return web.FileResponse(os.path.join(ROOT, 'client/favicon.png'))

async def remote_login(request):
    content = open(os.path.join(ROOT, 'client/remote-login.html'), 'r').read()
    return web.Response(content_type='text/html', text=content)

async def admin_page(request):
    content = open(os.path.join(ROOT, 'client/admin/index.html'), 'r').read()
    return web.Response(content_type='text/html', text=content)

async def preferences_handler(request):
    content = open(os.path.join(ROOT, 'client/admin/preferences.html'), 'r').read()
    return web.Response(content_type='text/html', text=content)

async def users_handler(request):
    content = open(os.path.join(ROOT, 'client/admin/users.html'), 'r').read()
    return web.Response(content_type='text/html', text=content)

async def do_login(request):
    os.environ['isLoggedIn'] = "True"
    os.environ['currTime'] = str(time.time())
    return web.Response(content_type='data/text', text="Logged in!")

async def get_prefs(request):
    peer = PeerConnectionFactory()
    try:
        username = os.environ['username']
        password = os.environ['password']
    except KeyError:
        username = "Not Applicable"
        password = "Not Applicable"
    content = {
        "idpconfig": json.dumps(peer.config),
        "stun_server": peer.STUN_SERVER,
        "turn_server": peer.TURN_SERVER,
        "turn_username": peer.TURN_USERNAME,
        "turn_password": peer.TURN_PASSWORD,
        "server_username": username,
        "server_password": password
    }
    return web.Response(content_type='text/json', text=json.dumps(content))

async def set_prefs(request):
    data = await request.post()
    data = variabledecode.variable_decode(data)
    logging.warning(data)
    os.environ['STUN_SERVER'] = data['stun_server']
    os.environ['TURN_SERVER'] = data['turn_server']
    os.environ['TURN_USERNAME'] = data['turn_username']
    os.environ['TURN_PASSWORD'] = data['turn_password']
    username = data['server_username']
    password = data['server_password']
    if ((username != "" and password != "") and (username != 'Not Applicable' or username != 'Not Applicable') ):
        os.environ['username'] = data['server_username']
        os.environ['password'] = data['server_password']
    return web.HTTPFound('/preferences')

async def is_logged_in(request):
    ws.send(jpg_base64)
    results=json.loads(ws.recv())
    for i in results['results']:
        # logging.warning(i)
        if i['label'] == "myface" and i['value'] >= 0.8:
            # return "True"
            os.environ['isLoggedIn'] = "True"
            os.environ['currTime'] = str(time.time())
            return web.Response(content_type='text/data', text="True")
    else:
        # return "False"
        if os.environ['isLoggedIn'] == "True" and float(os.environ['currTime']) > time.time() - 10:
            return web.Response(content_type='text/data', text="True")
        os.environ['isLoggedIn'] = "False"
        os.environ['currTime'] = str(time.time())
        return web.Response(content_type='text/data', text="False")

async def classification(request):
    cl_results = "{}"
    if jpg_base64 != "":
        print("Sending to classifier")
        ws.send(jpg_base64)
        cl_results=ws.recv()
        print(cl_results)
        print("Sending cl_results to client")
    return web.Response(content_type='application/json', text=cl_results)

async def offer(request):
    params = await request.json()
    offer = RTCSessionDescription(
        sdp=params['sdp'],
        type=params['type'])
    # Add local media
    pc = pc_factory.create_peer_connection()
    local_video = RTCVideoStream(camera_device)
    pcs.add(pc)
    pc.addTrack(local_video)
    @pc.on('connectionstatechange')
    async def on_connectionstatechange():
        if pc.iceConnectionState == 'failed':
            await pc.close()
            pcs.discard(pc)
    await pc.setRemoteDescription(offer)
    answer = await pc.createAnswer()
    await pc.setLocalDescription(answer)
    return web.Response(
        content_type='application/json',
        text=json.dumps({
            'sdp': pc.localDescription.sdp,
            'type': pc.localDescription.type
        }))

async def classify_remote(request):
    params = await request.json()
    image = params['data']
    image_data = image[image.find('base64,/')+7:]
    frame = Image.open(io.BytesIO(base64.b64decode(image_data)))
    encode_param = (int(cv2.IMWRITE_JPEG_QUALITY), 90)
    global jpg_base64
    frame = numpy.array(frame)
    frame = cv2.rotate(frame, cv2.ROTATE_90_COUNTERCLOCKWISE)
    gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
    face_cascade = cv2.CascadeClassifier('haarcascade_frontalface_alt2.xml')
    faces = face_cascade.detectMultiScale(gray,1.1,4)
    for (x, y, w, h) in faces:
        if h >= 160 and w >= 160:
            faces = frame[y-100:y+h+100,x-50:x+w+50]
        else:
            faces = frame
    try:
        jpg_base64 = cv2.resize(faces, (160, 160), interpolation = cv2.INTER_AREA)
    except:
        jpg_base64 = cv2.resize(frame, (160, 160), interpolation = cv2.INTER_AREA)
    jpg_base64 = cv2.cvtColor(jpg_base64 , cv2.COLOR_BGR2RGB)
    _frame, jpg_base64 = cv2.imencode('.jpg', jpg_base64, encode_param)
    jpg_base64 = base64.b64encode(jpg_base64) # save img as base64 to send over websocket
    ws.send(jpg_base64)
    out = json.loads(ws.recv())
    for i in out['results']:
        if i['label'] == "myface" and i['value'] >= 0.5:
            os.environ['isLoggedIn'] = "True"
            os.environ['currTime'] = str(time.time())
            # return "True"
            return web.Response(content_type='text/data', text="True")
    else:
        # return "False"
        return web.Response(content_type='text/data', text="False")

async def mjpeg_handler(request):
    boundary = "frame"
    response = web.StreamResponse(status=200, reason='OK', headers={
        'Content-Type': 'multipart/x-mixed-replace; '
                        'boundary=%s' % boundary,
    })
    await response.prepare(request)
    while True:
        data = await camera_device.get_jpeg_frame()
        #print(data)
        print("Sending to classifier")
        ws.send(jpg_base64)
        global cl_results
        cl_results=ws.recv()
        print(cl_results)
        await asyncio.sleep(0.2) # this means that the maximum FPS is 5
        await response.write(
            '--{}\r\n'.format(boundary).encode('utf-8'))
        await response.write(b'Content-Type: image/jpeg\r\n')
        await response.write('Content-Length: {}\r\n'.format(
                len(data)).encode('utf-8'))
        await response.write(b"\r\n")
        await response.write(data)
        await response.write(b"\r\n")
    return response

async def config(request):
    return web.Response(
        content_type='application/json',
        text=pc_factory.get_ice_config()
    )

async def on_shutdown(app):
    # close peer connections
    coros = [pc.close() for pc in pcs]
    ws.close()
    await asyncio.gather(*coros)

def checkDeviceReadiness():
    if not os.path.exists('/dev/video0') and platform.system() == 'Linux':
        print('Video device is not ready')
        print('Trying to load bcm2835-v4l2 driver...')
        os.system('bash -c "modprobe bcm2835-v4l2"')
        sleep(1)
        sys.exit()
    else:
        print('Video device is ready')
    try:
        create_connection("ws://edgeimpulse-inference:8080")
    except:
        sleep(10);

if __name__ == '__main__':
    checkDeviceReadiness()

    ROOT = os.path.dirname(__file__)
    camera_device = CameraDevice()
    pc_factory = PeerConnectionFactory()
    jpg_base64 = ""
    pcs = set()
    flip = False
    try:
        if os.environ['rotation'] == '1':
            flip = True
    except:
        pass

    auth = []
    if 'username' in os.environ and 'password' in os.environ:
        print('\n#############################################################')
        print('Authorization is enabled.')
        print('Your balenaCam is password protected.')
        print('#############################################################\n')
        auth.append(BasicAuthMiddleware(username = os.environ['username'], password = os.environ['password']))
    else:
        print('\n#############################################################')
        print('Authorization is disabled.')
        print('Anyone can access your balenaCam, using the device\'s URL!')
        print('Set the username and password environment variables \nto enable authorization.')
        print('For more info visit: \nhttps://github.com/balena-io-playground/balena-cam')
        print('#############################################################\n')

    # Factory to create peerConnections depending on the iceServers set by user
    # Connect to websocket server for image classification
    ws = create_connection("ws://edgeimpulse-inference:8080")

    app = web.Application(middlewares=auth)
    app.on_shutdown.append(on_shutdown)
    app.router.add_get('/', index)
    app.router.add_get('/favicon.png', favicon)
    app.router.add_get('/balena-logo.svg', balena_logo)
    app.router.add_get('/edgeimpulse-logo-white.svg', edgeimpulse_logo)
    app.router.add_get('/balena-cam.svg', balena)
    app.router.add_get('/client.js', javascript)
    app.router.add_get('/style.css', stylesheet)
    app.router.add_post('/offer', offer)
    app.router.add_get('/mjpeg', mjpeg_handler)
    app.router.add_get('/ice-config', config)
    app.router.add_get('/classification', classification)
    app.router.add_post('/classify-remote', classify_remote)
    app.router.add_get('/remote-login', remote_login)
    app.router.add_get('/isLoggedIn', is_logged_in)
    app.router.add_get('/admin', admin_page)
    app.router.add_get('/preferences',preferences_handler)
    app.router.add_get('/get_prefs', get_prefs)
    app.router.add_get('/users',users_handler)
    app.router.add_get('/doLogin', do_login)
    app.router.add_post('/setPrefs', set_prefs)
    web.run_app(app, port=80)
