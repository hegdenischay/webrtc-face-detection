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
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(title: Text(widget.title)),
      body: Center(
        child: Column(
          mainAxisAlignment: MainAxisAlignment.center,
          children: <Widget>[
            TextFormField(
                    validator: (value){
                        if (value == null){
                            return 'Please enter some text';
                        }
                        return value;
                    },
                    controller: _controller,
                    ),
            ElevatedButton(child: Text('Set the host'), onPressed: () {
                if(_controller.text != null){
                        var hostKey = 'host';
                        LocalStorageService.saveToDisk(hostKey, _controller.text );
                        Navigator.push(context,
                        MaterialPageRoute(builder: (context) => MyHomePage(title: 'Home')),
                                );
                }
            }),
          ],
        ),
      ),
    );
  }
}
