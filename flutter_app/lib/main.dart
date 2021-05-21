// import 'dart:io';
// import 'dart:convert';

import 'dart:async';
// import 'dart:html';
import 'package:flutter/services.dart';
import 'package:flutter_app/services/get_host.dart';
import 'package:http/http.dart' as http;
import 'package:flutter/material.dart';
import 'package:shared_preferences/shared_preferences.dart';
import 'service_locator.dart';
import 'host_view.dart';
import 'services/localstorage_service.dart';
import 'package:fluttertoast/fluttertoast.dart';
import 'package:camera/camera.dart';
import 'camera_view.dart';
import 'package:local_auth/local_auth.dart';
import 'package:http_auth/http_auth.dart';
import 'dart:convert';

Future<void> main() async {
  try {
    WidgetsFlutterBinding.ensureInitialized();
    setupLocator();
    saveHost();
    runApp(MyApp());
  } catch (error) {
    print('Locator Setup has failed');
  }
}

saveHost() async {
  var host = LocalStorageService.getFromDisk('host');
  var password = LocalStorageService.getFromDisk('password');
  var username = LocalStorageService.getFromDisk('username');
  if (host == "null") {
    LocalStorageService.saveToDisk("host", "unset");
  }
  if (password == "null") {
    LocalStorageService.saveToDisk("password", "unset");
  }
  if (username == "null") {
    LocalStorageService.saveToDisk("username", "unset");
  }
}

class MyApp extends StatelessWidget {
  // This widget is the root of your application.
  @override
  Widget build(BuildContext context) {
    return MaterialApp(
      title: 'DoorMate',
      theme: ThemeData(
          primarySwatch: Colors.lightBlue,
          textTheme: TextTheme(bodyText2: TextStyle(color: Colors.black))),
      //home: MyHomePage(title: 'Lock Status'),
      home: _getStartupScreen(),
      darkTheme: ThemeData.dark(),
      routes: {
        '/host': (context) => HostView(title: 'Set the webcame'),
        '/hostagain': (context) => HostView(title: 'Set The Host Again'),
      },
    );
  }
}

Widget _getStartupScreen() {
  var host = LocalStorageService.getFromDisk('host');
  final LocalAuthentication _localAuthentication = LocalAuthentication();
  bool _authorized = true;
  Future<bool> checkingForBioMetrics() async {
    bool canCheckBiometrics = await _localAuthentication.canCheckBiometrics;
    print(canCheckBiometrics);
    return canCheckBiometrics;
  }

  Future<void> _authenticateMe() async {
    bool authorized = false;
    try {
      authorized = await _localAuthentication.authenticate(
        localizedReason: "To access the lock", // message for dialogue
        stickyAuth: false,
        biometricOnly: true,
      );
      if(authorized == false){
          SystemNavigator.pop();
      }
    } catch (e) {
      print(e);
    }
  }

  _authenticateMe();
  print(host);
  if (host == 'unset' || host == null || host == 'null') {
    return HostView(title: 'Set The Webcam');
  } else {
    return MyHomePage(title: 'Lock Status');
  }
}

class MyHomePage extends StatefulWidget {
  MyHomePage({Key key, this.title}) : super(key: key);

  // This widget is the home page of your application. It is stateful, meaning
  // that it has a State object (defined below) that contains fields that affect
  // how it looks.

  // This class is the configuration for the state. It holds the values (in this
  // case the title) provided by the parent (in this case the App widget) and
  // used by the build method of the State. Fields in a Widget subclass are
  // always marked "final".

  final String title;

  @override
  _MyHomePageState createState() => _MyHomePageState();
}

class _MyHomePageState extends State<MyHomePage> {
  // int _counter = 0;
  bool _logged = false;
  Timer _timer;
  void _checkResponse() async {
    var localStorageService = locator<LocalStorageService>();
    var host = localStorageService.hasHost;

    print(host);
    if (host != 'unset' && host != null && host != 'null') {
      try {
        final response = await http.get(Uri.https(host, 'isLoggedIn'));
        _isLoggedIn(response);
        if (response.statusCode == 401) {
          throw ("exception!");
        }
      } catch (e, s) {
        try {
          var username = localStorageService.hasUser;
          // print(username);
          var password = localStorageService.hasPass;
          // print(password);
          Codec<String, String> stringtoBase64 = utf8.fuse(base64);
          String hash = stringtoBase64.encode(username + ":" + password);
          // print(hash);
          final response =
              await http.get(Uri.https(host, 'isLoggedIn'), headers: {
            'Authorization': 'Basic ' + hash,
          });
          print(response.statusCode);
          _isLoggedIn(response);
        } catch (e, s) {
          print("Exception");
        }
      }
    }
  }

  void _isLoggedIn(response) async {
    if (response.statusCode == 200) {
      if (response.body == "True") {
        // print(response.body);
        setState(() {
          _logged = true;
        });
      } else {
        if (response.body == "False") {
          setState(() {
            _logged = false;
          });
        }
        print(response.body);
      }
    } else {
      print("Exception!");
      setState(() {
        _logged = false;
      });
      // Navigator.pushReplacementNamed(context, '/hostagain');
      if (response.statusCode == 503) {
        Fluttertoast.showToast(
            msg: 'We were unable to contact the server',
            toastLength: Toast.LENGTH_SHORT,
            gravity: ToastGravity.CENTER,
            timeInSecForIosWeb: 1,
            backgroundColor: Colors.red,
            textColor: Colors.white,
            fontSize: 16.0);
      }
    }
  }

  // void _incrementCounter() {
  //   setState(() {
  // This call to setState tells the Flutter framework that something has
  // changed in this State, which causes it to rerun the build method below
  // so that the display can reflect the updated values. If we changed
  // _counter without calling setState(), then the build method would not be
  // called again, and so nothing would appear to happen.
  // _counter++;
  // });
  // }

  @override
  void initState() {
    super.initState();
    // makes sure that login is checked every 10 seconds
    _timer =
        Timer.periodic(Duration(seconds: 1), (Timer t) => _checkResponse());
  }

  void obliterate() {
    LocalStorageService.saveToDisk('host', 'unset');
  }

  @override
  Widget build(BuildContext context) {
    // final channel = WebSocketChannel.connect(Uri.parse('wss://'+_host+'/websocket'));
    // channel.stream.listen((message) {
    //     channel.sink.add('close');
    //     channel.sink.close(status.goingAway);
    // });
    // This method is rerun every time setState is called, for instance as done
    // by the _incrementCounter method above.
    //
    // The Flutter framework has been optimized to make rerunning build methods
    // fast, so that you can just rebuild anything that needs updating rather
    // than having to individually change instances of widgets.
    return Scaffold(
      appBar: AppBar(
        // Here we take the value from the MyHomePage object that was created by
        // the App.build method, and use it to set our appbar title.
        title: Text(widget.title),
      ),
      drawer: Drawer(
          child: ListView(padding: EdgeInsets.zero, children: <Widget>[
        DrawerHeader(
          decoration: BoxDecoration(color: Colors.blue),
        ),
        SafeArea(
            child: ListTile(
          title: Text('Preferences'),
          leading: Icon(Icons.block),
          onTap: () {
            // obliterate();
            // Fluttertoast.showToast(
            //     msg: "Data Cleared!",
            //     toastLength: Toast.LENGTH_SHORT,
            //     gravity: ToastGravity.CENTER,
            //     timeInSecForIosWeb: 1,
            //     backgroundColor: Colors.red,
            //     textColor: Colors.white,
            //     fontSize: 16.0);

            // obliterate();
            Navigator.popAndPushNamed(context, "/host");
          },
        )),
        SafeArea(
          child: ListTile(
              title: Text('RemoteLogin'),
              leading: Icon(Icons.camera),
              onTap: () async {
// Navigator.pop(context);
                final cameras = await availableCameras();
                final firstCamera = cameras[1];
                Navigator.push(
                    context,
                    MaterialPageRoute(
                        builder: (context) =>
                            TakePictureScreen(camera: firstCamera)));
              }),
        ),
        SafeArea(
          child: AboutListTile(
            icon: Icon(Icons.info),
            applicationIcon: FlutterLogo(),
            applicationName: 'SimulatedLock',
            applicationVersion: 'alpha',
          ),
        ),
      ])),
      body: Center(
        child: Column(
          mainAxisAlignment: MainAxisAlignment.center,
          children: <Widget>[
            Icon(
              _logged == true ? Icons.lock_open : Icons.lock,
              color: _logged == true ? Colors.green : Colors.red,
              size: 40.0,
            ),
            Text(
              _logged == true ? 'The Lock is unlocked.' : 'The lock is locked.',
            ),
          ],
        ),
      ),
    );
  }
}
