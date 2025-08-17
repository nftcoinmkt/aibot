import 'package:flutter/material.dart';
import 'package:flutter_ai_bot/models/channel_model.dart';
import 'package:flutter_ai_bot/network/api_service.dart';
import 'package:flutter_ai_bot/views/chat_view.dart';
import 'package:flutter_ai_bot/views/login_view.dart';

class HomeView extends StatefulWidget {
  final ApiService apiService;

  const HomeView({super.key, required this.apiService});

  @override
  _HomeViewState createState() => _HomeViewState();
}

class _HomeViewState extends State<HomeView> with SingleTickerProviderStateMixin {
  late Future<List<Channel>> _channelsFuture;

  @override
  void initState() {
    super.initState();
    _channelsFuture = widget.apiService.getChannels();
  }

  void _logout() async {
    await widget.apiService.signout();
    if (!mounted) return;
    Navigator.pushAndRemoveUntil(
      context,
      MaterialPageRoute(builder: (context) => LoginView(apiService: widget.apiService)),
      (route) => false,
    );
  }

  void _createChannel() {
    final _formKey = GlobalKey<FormState>();
    final _nameController = TextEditingController();
    final _descriptionController = TextEditingController();

    showDialog(
      context: context,
      builder: (context) {
        return AlertDialog(
          title: Text('Create Channel'),
          content: Form(
            key: _formKey,
            child: Column(
              mainAxisSize: MainAxisSize.min,
              children: [
                TextFormField(
                  controller: _nameController,
                  decoration: InputDecoration(labelText: 'Channel Name'),
                  validator: (value) {
                    if (value == null || value.isEmpty) {
                      return 'Please enter a name';
                    }
                    return null;
                  },
                ),
                TextFormField(
                  controller: _descriptionController,
                  decoration: InputDecoration(labelText: 'Description'),
                  validator: (value) {
                    if (value == null || value.isEmpty) {
                      return 'Please enter a description';
                    }
                    return null;
                  },
                ),
              ],
            ),
          ),
          actions: [
            TextButton(
              onPressed: () => Navigator.pop(context),
              child: Text('Cancel'),
            ),
            ElevatedButton(
              onPressed: () async {
                if (_formKey.currentState!.validate()) {
                  try {
                    await widget.apiService.createChannel(
                      _nameController.text,
                      _descriptionController.text,
                    );
                    Navigator.pop(context);
                    setState(() {
                      _channelsFuture = widget.apiService.getChannels();
                    });
                  } catch (e) {
                    // TODO: Show error
                    print('Failed to create channel: $e');
                  }
                }
              },
              child: Text('Create'),
            ),
          ],
        );
      },
    );
  }

  @override
  Widget build(BuildContext context) {
    return DefaultTabController(
      length: 3,
      child: Scaffold(
        appBar: AppBar(
          title: Text('WhatsApp'),
          actions: [
            IconButton(
              icon: Icon(Icons.search),
              onPressed: () {},
            ),
            IconButton(
              icon: Icon(Icons.more_vert),
              onPressed: _logout, // For now, this will be logout
            ),
          ],
          bottom: TabBar(
            indicatorColor: Colors.white,
            tabs: [
              Tab(text: 'CHATS'),
              Tab(text: 'STATUS'),
              Tab(text: 'CALLS'),
            ],
          ),
        ),
        body: TabBarView(
          children: [
            // Chats Tab
            FutureBuilder<List<Channel>>(
              future: _channelsFuture,
              builder: (context, snapshot) {
                if (snapshot.connectionState == ConnectionState.waiting) {
                  return Center(child: CircularProgressIndicator());
                } else if (snapshot.hasError) {
                  return Center(child: Text('Error: ${snapshot.error}'));
                } else if (!snapshot.hasData || snapshot.data!.isEmpty) {
                  return Center(child: Text('No channels found.'));
                } else {
                  final channels = snapshot.data!;
                  return ListView.builder(
                    itemCount: channels.length,
                    itemBuilder: (context, index) {
                      final channel = channels[index];
                      return ListTile(
                        leading: CircleAvatar(
                          backgroundColor: Theme.of(context).primaryColor,
                          child: Text(channel.name.isNotEmpty ? channel.name[0] : ''),
                        ),
                        title: Text(channel.name, style: TextStyle(fontWeight: FontWeight.bold)),
                        subtitle: Text(channel.description, maxLines: 1, overflow: TextOverflow.ellipsis),
                        onTap: () {
                          Navigator.push(
                            context,
                            MaterialPageRoute(
                              builder: (context) => ChatView(
                                channel: channel,
                                apiService: widget.apiService,
                              ),
                            ),
                          );
                        },
                      );
                    },
                  );
                }
              },
            ),
            // Status Tab
            Center(child: Text('Status feature coming soon!')),
            // Calls Tab
            Center(child: Text('Calls feature coming soon!')),
          ],
        ),
        floatingActionButton: FloatingActionButton(
          onPressed: _createChannel,
          child: Icon(Icons.add),
          backgroundColor: Theme.of(context).colorScheme.secondary,
        ),
      ),
    );
  }
}

