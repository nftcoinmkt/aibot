class Channel {
  final int id;
  final String name;
  final String description;

  Channel({required this.id, required this.name, required this.description});

  factory Channel.fromJson(Map<String, dynamic> json) {
    return Channel(
      id: json['id'],
      name: json['name'],
      description: json['description'],
    );
  }
}
