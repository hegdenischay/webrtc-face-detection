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

#import ssl

#ssl_ctx = ssl.create_default_context(ssl.Purpose.CLIENT_AUTH)
#ssl_ctx.load_cert_chain('domain_srv.crt', 'domain_srv.key')


class CameraDevice():
    def __init__(self):
        self.cap = cv2.VideoCapture(0)
        ret, frame = self.cap.read()
        if not ret:
            print('Failed to open default camera. Exiting...')
            sys.exit()
        self.cap.set(3, 640)
        self.cap.set(4, 640)

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
        jpg_base64 = cv2.resize(frame, (96, 96), interpolation = cv2.INTER_AREA)
        _frame, jpg_base64 = cv2.imencode('.jpg', jpg_base64, encode_param)
        jpg_base64 = base64.b64encode(jpg_base64) # save img as base64 to send over websocket
        #print(jpg_base64)

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


        self.STUN_SERVER = 'stun:stun.l.google.com:19302'
        self.TURN_SERVER = 'turn:numb.viagenie.ca'
        self.TURN_USERNAME = 'orgoanon@getnada.com'
        self.TURN_PASSWORD = 'orgoanon'
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
        # self.config['iceServers'] = []
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

async def peer_add(request):
    content = open(os.path.join(ROOT, 'client/invite.html'), 'r').read()
    return web.Response(content_type='text/html', text=content)

async def stylesheet(request):
    content = open(os.path.join(ROOT, 'client/style.css'), 'r').read()
    return web.Response(content_type='text/css', text=content)

async def javascript(request):
    content = open(os.path.join(ROOT, 'client/client.js'), 'r').read()
    return web.Response(content_type='application/javascript', text=content)

async def invited(request):
    content = open(os.path.join(ROOT, 'client/invited.js'), 'r').read()
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

async def vid_page(request):
    content = open(os.path.join(ROOT, 'client/vid.html'), 'r').read()
    return web.Response(content_type='text/html', text=content)

async def preferences_handler(request):
    content = open(os.path.join(ROOT, 'admin/preferences.html'), 'r').read()
    return web.Response(content_type='text/html', text=content)

async def users_handler(request):
    content = open(os.path.join(ROOT, 'admmin/users.html'), 'r').read()
    return web.Response(content_type='text/html', text=content)

async def websocket_handler(request):
    logging.warn('Yoo hoo!')
    ws = web.WebSocketResponse()
    await ws.prepare(request)
    await ws.send_str("Just werks!")
    # msg = await ws.receive_str()
    async for msg in ws:
        if msg.type == aiohttp.WSMsgType.TEXT:
            if msg == 'close':
                await ws.close()
                break
            else:
                reply = await is_logged_in(request)
                await ws.send_str(reply)
        elif msg.type == aiohttp.WSMsgType.ERROR:
            print('ws exception')

    print('websocket connection closed')
    return ws

async def is_logged_in(request):
    # return web.Response(content_type='text/html', text=jpg_base64)
    # pass
    #_ = await RTCVideoStream.recv()
    ws.send(jpg_base64)
    results=json.loads(ws.recv())
    for i in results['results']:
        logging.warning(i)
        if i['label'] == "myface" and i['value'] >= 0.8:
            # return "True"
            return web.Response(content_type='text/data', text="True")
    else:
        # return "False"
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
    params = await request.json();
    logging.warning(params['data'][:200])
    image = params['data'];
    image_data = image[image.find('base64,/')+7:]
    logging.warning(image_data[:200])
    frame = imread(io.BytesIO(base64.b64decode(image_data)))
    encode_param = (int(cv2.IMWRITE_JPEG_QUALITY), 90)
    global jpg_base64
    jpg_base64 = cv2.resize(frame, (96, 96), interpolation = cv2.INTER_AREA)
    _frame, jpg_base64 = cv2.imencode('.jpg', jpg_base64, encode_param)
    jpg_base64 = base64.b64encode(jpg_base64) # save img as base64 to send over websocket
    ws.send(jpg_base64)
    out = json.loads(ws.recv())
    logging.warning(out)
    for i in out['results']:
        logging.warning(i)
        if i['label'] == "myface" and i['value'] >= 0.8:
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

async def peer_camera(request):
    params = await request.json()
    offer = RTCSessionDescription(
        sdp=params['sdp'],
        type=params['type'])
    #pc_id = "PeerConnection(%s)" % uuid.uuid4()
    #player = 
    pc = pc_factory.create_peer_connection()
    #video = pc.getReceivers[0].track
    pcs.add(pc)
    #pc.addTrack(video)

    @pc.on("datachannel")
    def on_datachannel(channel):
        @channel.on("message")
        def on_message(message):
            if isinstance(message, str) and message.startswith("ping"):
                channel.send("pong" + message[4:])

    @pc.on("connectionstatechange")
    async def on_connectionstatechange():
        print("ICE connection state is", pc.iceConnectionState)
        if pc.iceConnectionState == "failed":
            await pc.close()
            pcs.discard(pc)

    @pc.on("track")
    def on_track(track):
        print("Track received", track.kind)

        if track.kind == "audio":
            pc.addTrack(track)
            #recorder.addTrack(track)
        elif track.kind == "video":
            pc.addTrack(track)
            #recorder.addTrack(track)
        @track.on("ended")
        async def on_ended():
            print("Track ended", track.kind)
            await pc.stop()

    # handle offer
    await pc.setRemoteDescription(offer)
    #await recorder.start()

    # send answer
    answer = await pc.createAnswer()
    await pc.setLocalDescription(answer)

    return web.Response(
        content_type="application/json",
        text=json.dumps(
            {"sdp": pc.localDescription.sdp, "type": pc.localDescription.type}
        ),
    )

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
    app.router.add_get('/invite', peer_add)
    app.router.add_get('/invited.js', invited)
    app.router.add_post('/offer-remote', peer_camera)
    app.router.add_post('/classify-remote', classify_remote)
    app.router.add_get('/remote-login', remote_login)
    app.router.add_get('/isLoggedIn', is_logged_in)
    app.router.add_get('/admin', admin_page)
    app.router.add_get('/vid.html',vid_page)
    app.router.add_get('/websocket', websocket_handler)
    app.router.add_get('/preferences',preferences_handler)
    app.router.add_get('/users',users_handler)
    web.run_app(app, port=80)
