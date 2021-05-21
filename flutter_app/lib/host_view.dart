import 'package:flutter/material.dart';
import 'services/localstorage_service.dart';
import 'service_locator.dart';
import 'main.dart';

class HostView extends StatefulWidget {
  HostView({Key key, this.title}) : super(key: key);

  final String title;

  @override
  _HostViewState createState() => _HostViewState();
}

class _HostViewState extends State<HostView> {
  @override
  final _formKey = GlobalKey<FormState>();
  final _controller = TextEditingController();
final _controller2 = TextEditingController();
 final _controller3 = TextEditingController();


  final host = LocalStorageService.getFromDisk('host');
  final username = LocalStorageService.getFromDisk('username');
  final password = LocalStorageService.getFromDisk('password');
  Widget build(BuildContext context) {
    String hostisfine = (host != 'unset' || host != 'null') ? host : 'Host *';
    String usernamefine =
        (username != 'unset' || username != 'null') ? username : 'Username';
    String passwordfine =
        (password != 'unset' || password != 'null') ? password : 'Password';
    return Scaffold(
      appBar: AppBar(title: Text(widget.title)),
      body: Center(
        child: Column(
          mainAxisAlignment: MainAxisAlignment.center,
          children: <Widget>[
            TextFormField(
              decoration: InputDecoration(
                icon: Icon(Icons.public),
                hintText: 'The domain name or IP Address of the webcam',
                labelText: hostisfine,
                border: OutlineInputBorder(),
              ),
              validator: (value) {
                if (_controller.text == null ||
                    _controller.text == "" ||
                    _controller.text == "unset") {
                  return 'Please enter some text';
                }
                return value;
              },
              controller: _controller,
            ),
            TextFormField(
              decoration: InputDecoration(
                icon: Icon(Icons.person),
                hintText: 'The username of the server',
                labelText: usernamefine,
                border: OutlineInputBorder(),
              ),
              validator: (value) {
                return value;
              },
              controller: _controller2,
            ),
            TextFormField(
              decoration: InputDecoration(
                icon: Icon(Icons.person),
                hintText: 'The password of the server',
                labelText: password,
                border: OutlineInputBorder(),
              ),
              validator: (value) {
                return value;
              },
              controller: _controller3,
            ),
            ElevatedButton(
                child: Text('Save Values'),
                onPressed: () {
                  if (_controller.text != null &&
                      _controller.text != '' &&
                      _controller.text != 'unset') {
                    var hostKey = 'host';
                    LocalStorageService.saveToDisk(hostKey, _controller.text);
                    LocalStorageService.saveToDisk('username', _controller2.text);
                    LocalStorageService.saveToDisk('password',_controller3.text);
                    Navigator.pushReplacement(
                      context,
                      MaterialPageRoute(
                          builder: (context) =>
                              MyHomePage(title: 'Lock Status')),
                    );
                  }
                }),
          ],
        ),
      ),
    );
  }
}
