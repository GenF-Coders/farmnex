import 'package:flutter/material.dart';
import 'package:provider/provider.dart';

import '../../providers/logistics_provider.dart';
import '../../widgets/auto_translated_text.dart';
import 'driver_location.dart';

const Map<String, String> _vehicleTypes = {
  'pickup': '🛻 Pickup',
  'tempo': '🚚 Tempo',
  'mini_truck': '🚐 Mini truck',
  'truck': '🚛 Truck',
};

/// Asks the driver for the truck's details and registers it. The truck's home base is the
/// phone's current position (the optimizer needs coordinates). Returns true when registered.
Future<bool> showVehicleDialog(BuildContext context) async {
  final done = await showDialog<bool>(
    context: context,
    builder: (_) => const _VehicleDialog(),
  );
  return done ?? false;
}

class _VehicleDialog extends StatefulWidget {
  const _VehicleDialog();

  @override
  State<_VehicleDialog> createState() => _VehicleDialogState();
}

class _VehicleDialogState extends State<_VehicleDialog> {
  final _number = TextEditingController();
  final _capacity = TextEditingController(text: '1000');
  final _rate = TextEditingController(text: '12');
  final _base = TextEditingController();
  String _type = 'tempo';
  bool _cold = false;
  bool _saving = false;
  String? _message;

  @override
  void dispose() {
    for (final c in [_number, _capacity, _rate, _base]) {
      c.dispose();
    }
    super.dispose();
  }

  Future<void> _save() async {
    final number = _number.text.trim().toUpperCase();
    final capacity = double.tryParse(_capacity.text.trim());
    final rate = double.tryParse(_rate.text.trim());
    if (number.length < 4) return setState(() => _message = 'Enter the vehicle number.');
    if (capacity == null || capacity <= 0 || capacity > 40000) {
      return setState(() => _message = 'Capacity must be between 1 and 40000 kg.');
    }
    if (rate == null || rate <= 0) return setState(() => _message = 'Enter the rate per tonne per km.');

    setState(() {
      _saving = true;
      _message = null;
    });
    final position = await currentDriverPosition();
    if (!mounted) return;
    if (position == null) {
      return setState(() {
        _saving = false;
        _message = 'Turn on location and allow it. Your truck\'s home base is where you are now.';
      });
    }
    final logistics = context.read<LogisticsProvider>();
    final error = await logistics.registerVehicle(
      vehicleNumber: number,
      vehicleType: _type,
      capacityKg: capacity,
      ratePerTonKm: rate,
      refrigerated: _cold,
      baseLat: position.latitude,
      baseLng: position.longitude,
      baseLabel: _base.text.trim(),
    );
    if (!mounted) return;
    if (error == null) {
      Navigator.of(context).pop(true);
    } else {
      setState(() {
        _saving = false;
        _message = error;
      });
    }
  }

  @override
  Widget build(BuildContext context) {
    return AlertDialog(
      shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(22)),
      title: const AutoTranslatedText('🚚 Register your truck', style: TextStyle(fontSize: 16, fontWeight: FontWeight.w900)),
      content: SingleChildScrollView(
        child: Column(
          mainAxisSize: MainAxisSize.min,
          children: [
            TextField(
              controller: _number,
              textCapitalization: TextCapitalization.characters,
              decoration: const InputDecoration(labelText: 'Vehicle number (MH12AB1234)'),
            ),
            const SizedBox(height: 8),
            DropdownButtonFormField<String>(
              initialValue: _type,
              decoration: const InputDecoration(labelText: 'Vehicle type'),
              items: _vehicleTypes.entries
                  .map((e) => DropdownMenuItem(value: e.key, child: AutoTranslatedText(e.value)))
                  .toList(),
              onChanged: (v) => setState(() => _type = v ?? _type),
            ),
            const SizedBox(height: 8),
            TextField(
              controller: _capacity,
              keyboardType: TextInputType.number,
              decoration: const InputDecoration(labelText: 'Capacity (kg)'),
            ),
            const SizedBox(height: 8),
            TextField(
              controller: _rate,
              keyboardType: const TextInputType.numberWithOptions(decimal: true),
              decoration: const InputDecoration(labelText: 'Rate (₹ per tonne per km)'),
            ),
            const SizedBox(height: 8),
            TextField(
              controller: _base,
              decoration: const InputDecoration(labelText: 'Home base name (optional)'),
            ),
            SwitchListTile(
              contentPadding: EdgeInsets.zero,
              value: _cold,
              onChanged: (v) => setState(() => _cold = v),
              title: const AutoTranslatedText('❄️ Refrigerated', style: TextStyle(fontSize: 13)),
            ),
            if (_message != null)
              Padding(
                padding: const EdgeInsets.only(top: 6),
                child: AutoTranslatedText(_message!, style: const TextStyle(fontSize: 11.5, color: Colors.red)),
              ),
          ],
        ),
      ),
      actions: [
        TextButton(
          onPressed: _saving ? null : () => Navigator.of(context).pop(false),
          child: const AutoTranslatedText('Cancel'),
        ),
        ElevatedButton(
          style: ElevatedButton.styleFrom(minimumSize: const Size(0, 48)),
          onPressed: _saving ? null : _save,
          child: _saving
              ? const SizedBox(width: 18, height: 18, child: CircularProgressIndicator(strokeWidth: 2))
              : const AutoTranslatedText('Register'),
        ),
      ],
    );
  }
}
