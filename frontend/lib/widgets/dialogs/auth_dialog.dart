import 'dart:async';

import 'package:flutter/material.dart';
import 'package:flutter/services.dart';
import 'package:provider/provider.dart';

import '../../core/theme/app_theme.dart';
import '../../models/user_model.dart';
import '../../providers/auth_provider.dart';
import '../auto_translated_text.dart';

/// Login / sign-up with a one-time code.
///
/// Sign-up is two server steps: verify the code (this USES it up), then create the account. If the
/// second step fails, the proof from the first step is kept, so "Try again" only repeats the second
/// step instead of re-sending a code that is already used.
class AuthDialog extends StatefulWidget {
  final String? reason;
  final UserRole initialRole;
  const AuthDialog({super.key, this.reason, this.initialRole = UserRole.farmer});
  @override
  State<AuthDialog> createState() => _AuthDialogState();
}

class _AuthDialogState extends State<AuthDialog> {
  bool _signup = false;
  bool _otpSent = false;
  UserRole _role = UserRole.farmer;
  final _mobile = TextEditingController();
  final _otp = TextEditingController();
  final _name = TextEditingController();
  final _surname = TextEditingController();
  final _dob = TextEditingController();
  final _address = TextEditingController();
  final _company = TextEditingController();
  String _gender = 'Male';
  String? _error;
  String? _info;
  int _resendIn = 0;
  bool _busy = false; // the whole verify -> create account -> save profile run
  Timer? _timer;

  @override
  void initState() {
    super.initState();
    // Admins are made by a script, not by public sign-up.
    _role = widget.initialRole == UserRole.admin ? UserRole.farmer : widget.initialRole;
  }

  @override
  void dispose() {
    _timer?.cancel();
    for (final c in [_mobile, _otp, _name, _surname, _dob, _address, _company]) {
      c.dispose();
    }
    super.dispose();
  }

  String get _digits => _mobile.text.replaceAll(RegExp(r'\D'), '');

  void _startCountdown(int seconds) {
    _timer?.cancel();
    setState(() => _resendIn = seconds <= 0 ? 30 : seconds);
    _timer = Timer.periodic(const Duration(seconds: 1), (t) {
      if (!mounted) return t.cancel();
      setState(() => _resendIn = _resendIn > 0 ? _resendIn - 1 : 0);
      if (_resendIn == 0) t.cancel();
    });
  }

  /// Back to step 1 (new number, or Login <-> Register).
  void _restart({bool? signup}) {
    if (_busy || context.read<AuthProvider>().isLoading) return; // a reply could otherwise land after the reset
    _timer?.cancel();
    context.read<AuthProvider>().resetAuthFlow();
    setState(() {
      if (signup != null) _signup = signup;
      _otpSent = false;
      _otp.clear();
      _error = null;
      _info = null;
      _resendIn = 0;
    });
  }

  Future<void> _sendCode({bool resend = false}) async {
    if (_digits.length < 10) {
      setState(() => _error = 'Enter your 10-digit mobile number.');
      return;
    }
    if (_signup && _name.text.trim().isEmpty) {
      setState(() => _error = 'Please enter your name.');
      return;
    }
    final a = context.read<AuthProvider>();
    final bool ok;
    if (resend) {
      ok = _signup ? await a.resendRegistrationOtp() : await a.resendLoginOtp();
    } else {
      ok = _signup ? await a.requestRegistrationOtp(phone: _mobile.text) : await a.requestLoginOtp(phone: _mobile.text);
    }
    if (!mounted) return;
    setState(() {
      _otpSent = _otpSent || ok;
      _error = ok ? null : _friendly(a.errorMessage);
      _info = ok ? 'Code sent to +91 ••••••${_digits.substring(_digits.length - 4)}. It arrives on WhatsApp or SMS.' : null;
      if (ok) _otp.clear();
    });
    if (ok) _startCountdown(a.lastOtpResponse?.resendAvailableInSeconds ?? 30);
  }

  Future<void> _verify() async {
    if (_busy || context.read<AuthProvider>().isLoading) return;
    setState(() => _busy = true);
    try {
      await _verifySteps();
    } finally {
      if (mounted) setState(() => _busy = false);
    }
  }

  Future<void> _verifySteps() async {
    final a = context.read<AuthProvider>();
    final code = _otp.text.trim();
    // A sign-up whose code was already accepted only needs the account step again.
    final needCode = !(_signup && a.hasRegistrationProof);
    if (needCode && code.length != 6) {
      setState(() => _error = 'Enter the 6-digit code.');
      return;
    }
    setState(() => _error = null);
    bool ok;
    if (_signup) {
      if (needCode && !await a.verifyRegistrationOtp(otp: code)) {
        if (mounted) setState(() => _error = _friendly(a.errorMessage));
        return;
      }
      ok = await a.completeRegistration(role: _role);
      if (ok) {
        await a.updateMyProfile(
          name: '${_name.text.trim()} ${_surname.text.trim()}'.trim(),
          surname: _surname.text.trim(),
          dateOfBirth: _dob.text.trim(),
          gender: _gender,
          address: _address.text.trim(),
          companyName: _company.text.trim().isEmpty ? null : _company.text.trim(),
        );
      }
    } else {
      ok = await a.verifyLoginOtp(otp: code);
    }
    if (!mounted) return;
    if (ok) {
      Navigator.of(context).pop(true);
    } else {
      setState(() => _error = _friendly(a.errorMessage));
    }
  }

  /// Server messages, made clear for a farmer (and pointing at the fix where there is one).
  String _friendly(String? message) {
    final m = message ?? 'Something went wrong. Please try again.';
    final lower = m.toLowerCase();
    if (lower.contains('invalid registration role')) {
      return 'This account type cannot sign up yet. Please choose another, or ask the FarmNex team. ($m)';
    }
    if (lower.contains('registration token')) {
      // The code was fine; the server could not check its own sign-up pass (a server setting).
      return 'Your number is verified, but the server could not finish creating the account. '
          'Please tell the FarmNex team. ($m)';
    }
    if (lower.contains('already been used')) {
      return 'This code was already used. Tap "Resend code" for a new one.';
    }
    if (lower.contains('expired')) return 'This code has expired. Tap "Resend code" for a new one.';
    if (lower.contains('already exists')) return 'This number already has an account. Please use Login.';
    if (lower.contains('invalid phone number or account')) return 'No account with this number yet. Please Register first.';
    return m;
  }

  @override
  Widget build(BuildContext context) {
    final a = context.watch<AuthProvider>();
    final proofKept = _signup && a.hasRegistrationProof;
    return Dialog(
      backgroundColor: AppTheme.cream,
      clipBehavior: Clip.antiAlias,
      insetPadding: const EdgeInsets.symmetric(horizontal: 16, vertical: 22),
      shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(26)),
      child: ConstrainedBox(
        constraints: const BoxConstraints(maxWidth: 420, maxHeight: 820),
        child: SingleChildScrollView(
          child: Column(crossAxisAlignment: CrossAxisAlignment.stretch, children: [
            _header(context),
            Padding(
              padding: const EdgeInsets.fromLTRB(20, 18, 20, 22),
              child: Column(crossAxisAlignment: CrossAxisAlignment.stretch, children: [
                _modeSwitch(),
                const SizedBox(height: 16),
                if (widget.reason != null) ...[
                  AutoTranslatedText(widget.reason!, style: const TextStyle(fontSize: 14, color: AppTheme.textMuted)),
                  const SizedBox(height: 12),
                ],
                if (_signup && !_otpSent) ..._signupFields(),
                if (!_otpSent) _phoneField(),
                if (_otpSent) ..._codeStep(proofKept),
                if (_error != null) _note(_error!, error: true),
                if (_info != null && _error == null) _note(_info!),
                const SizedBox(height: 4),
                SizedBox(
                  height: 54,
                  child: ElevatedButton(
                    onPressed: a.isLoading || _busy ? null : (_otpSent ? _verify : _sendCode),
                    child: a.isLoading || _busy
                        ? const SizedBox(width: 22, height: 22, child: CircularProgressIndicator(strokeWidth: 2.4, color: Colors.white))
                        : AutoTranslatedText(!_otpSent
                            ? 'Send code'
                            : proofKept
                                ? 'Try again'
                                : (_signup ? 'Verify & create account' : 'Verify & log in')),
                  ),
                ),
                const SizedBox(height: 12),
                const Row(mainAxisAlignment: MainAxisAlignment.center, children: [
                  Icon(Icons.lock_outline_rounded, size: 15, color: AppTheme.textMuted),
                  SizedBox(width: 6),
                  Flexible(child: AutoTranslatedText('Secure sign-in with a one-time code. No password needed.', textAlign: TextAlign.center, style: TextStyle(fontSize: 12.5, color: AppTheme.textMuted))),
                ]),
              ]),
            ),
          ]),
        ),
      ),
    );
  }

  Widget _header(BuildContext context) => Container(
        padding: const EdgeInsets.fromLTRB(22, 18, 8, 22),
        decoration: const BoxDecoration(gradient: AppTheme.brandGradient),
        child: Row(crossAxisAlignment: CrossAxisAlignment.start, children: [
          Expanded(
            child: Column(crossAxisAlignment: CrossAxisAlignment.start, children: [
              Row(children: [
                Container(
                  width: 34,
                  height: 34,
                  decoration: BoxDecoration(color: Colors.white.withValues(alpha: .15), borderRadius: BorderRadius.circular(10)),
                  child: const Icon(Icons.eco_rounded, color: AppTheme.harvestGold, size: 21),
                ),
                const SizedBox(width: 10),
                const AutoTranslatedText('FarmNex', style: TextStyle(fontSize: 22, fontWeight: FontWeight.w900, color: Colors.white, letterSpacing: -0.4)),
              ]),
              const SizedBox(height: 14),
              AutoTranslatedText(_signup ? 'Join FarmNex' : 'Welcome back',
                  style: const TextStyle(fontSize: 24, fontWeight: FontWeight.w900, color: Colors.white, height: 1.15)),
              const SizedBox(height: 4),
              const AutoTranslatedText('Your harvest. Your price.', style: TextStyle(fontSize: 15, color: AppTheme.goldSoft, fontWeight: FontWeight.w600)),
            ]),
          ),
          IconButton(
            onPressed: () => Navigator.pop(context),
            tooltip: 'Close',
            icon: const Icon(Icons.close_rounded, color: Colors.white),
          ),
        ]),
      );

  Widget _modeSwitch() => Container(
        padding: const EdgeInsets.all(4),
        decoration: BoxDecoration(color: const Color(0xFFEDE9DF), borderRadius: BorderRadius.circular(14)),
        child: Row(children: [
          Expanded(child: _modeTab('Login', !_signup, () => _restart(signup: false))),
          Expanded(child: _modeTab('Register', _signup, () => _restart(signup: true))),
        ]),
      );

  Widget _modeTab(String text, bool selected, VoidCallback onTap) => InkWell(
        onTap: selected ? null : onTap,
        borderRadius: BorderRadius.circular(11),
        child: AnimatedContainer(
          duration: const Duration(milliseconds: 180),
          padding: const EdgeInsets.symmetric(vertical: 11),
          decoration: BoxDecoration(
            color: selected ? Colors.white : Colors.transparent,
            borderRadius: BorderRadius.circular(11),
            boxShadow: selected ? AppTheme.softShadow : null,
          ),
          alignment: Alignment.center,
          child: AutoTranslatedText(text,
              style: TextStyle(fontSize: 15, fontWeight: selected ? FontWeight.w800 : FontWeight.w600, color: selected ? AppTheme.primaryGreen : AppTheme.textMuted)),
        ),
      );

  List<Widget> _signupFields() => [
        const AutoTranslatedText('I am a', style: TextStyle(fontSize: 14, fontWeight: FontWeight.w800, color: AppTheme.textDark)),
        const SizedBox(height: 8),
        Row(children: [
          _roleTile(UserRole.farmer, 'Farmer', '🧑‍🌾'),
          const SizedBox(width: 8),
          _roleTile(UserRole.buyer, 'Buyer', '🛒'),
          const SizedBox(width: 8),
          _roleTile(UserRole.logistics, 'Driver', '🚚'),
        ]),
        const SizedBox(height: 14),
        _field(_name, 'Name', Icons.person_outline_rounded, action: TextInputAction.next),
        _field(_surname, 'Surname', Icons.badge_outlined, action: TextInputAction.next),
        Padding(
          padding: const EdgeInsets.only(bottom: 10),
          child: TextField(
            controller: _dob,
            readOnly: true,
            decoration: _dec('Date of birth', Icons.calendar_today_outlined),
            onTap: () async {
              final d = await showDatePicker(context: context, firstDate: DateTime(1940), lastDate: DateTime.now(), initialDate: DateTime(2000));
              if (d != null) {
                _dob.text = '${d.year.toString().padLeft(4, '0')}-${d.month.toString().padLeft(2, '0')}-${d.day.toString().padLeft(2, '0')}';
              }
            },
          ),
        ),
        Padding(
          padding: const EdgeInsets.only(bottom: 10),
          child: DropdownButtonFormField<String>(
            initialValue: _gender,
            decoration: _dec('Gender', Icons.wc_rounded),
            items: const [
              DropdownMenuItem(value: 'Male', child: AutoTranslatedText('Male')),
              DropdownMenuItem(value: 'Female', child: AutoTranslatedText('Female')),
              DropdownMenuItem(value: 'Other', child: AutoTranslatedText('Other')),
            ],
            onChanged: (v) => setState(() => _gender = v ?? _gender),
          ),
        ),
        _field(_address, 'Village / city', Icons.location_on_outlined, action: TextInputAction.next),
        if (_role != UserRole.farmer)
          _field(_company, _role == UserRole.logistics ? 'Vehicle (e.g. Tata Ace)' : 'Shop / company name', Icons.business_outlined, action: TextInputAction.next),
      ];

  Widget _phoneField() => Padding(
        padding: const EdgeInsets.only(bottom: 10),
        child: TextField(
          controller: _mobile,
          keyboardType: TextInputType.phone,
          textInputAction: TextInputAction.done,
          inputFormatters: [FilteringTextInputFormatter.digitsOnly, LengthLimitingTextInputFormatter(10)],
          style: const TextStyle(fontSize: 18, fontWeight: FontWeight.w700, letterSpacing: 1),
          onSubmitted: (_) => _sendCode(),
          decoration: _dec('Mobile number', Icons.phone_iphone_rounded).copyWith(
            prefixText: '+91  ',
            prefixStyle: const TextStyle(fontSize: 18, fontWeight: FontWeight.w700, color: AppTheme.textDark),
          ),
        ),
      );

  List<Widget> _codeStep(bool proofKept) {
    if (proofKept) {
      // The code was accepted; only the account step failed. No new code is needed.
      return [_note('Your number is verified. Tap "Try again" to finish creating your account.')];
    }
    return [
      Row(children: [
        Expanded(
          child: AutoTranslatedText('Enter the 6-digit code', style: const TextStyle(fontSize: 15, fontWeight: FontWeight.w800)),
        ),
        TextButton(onPressed: () => _restart(), child: const AutoTranslatedText('Change number')),
      ]),
      const SizedBox(height: 6),
      TextField(
        controller: _otp,
        autofocus: true,
        keyboardType: TextInputType.number,
        textAlign: TextAlign.center,
        inputFormatters: [FilteringTextInputFormatter.digitsOnly, LengthLimitingTextInputFormatter(6)],
        style: const TextStyle(fontSize: 28, fontWeight: FontWeight.w900, letterSpacing: 12),
        decoration: _dec('', Icons.lock_clock_outlined).copyWith(labelText: null, hintText: '••••••', prefixIcon: null),
        // Verify by itself once all 6 digits are typed or pasted.
        onChanged: (v) {
          if (v.length == 6) _verify();
        },
      ),
      Align(
        alignment: Alignment.centerRight,
        child: TextButton(
          onPressed: _resendIn > 0 || context.watch<AuthProvider>().isLoading ? null : () => _sendCode(resend: true),
          child: AutoTranslatedText(_resendIn > 0 ? 'Resend code in ${_resendIn}s' : 'Resend code'),
        ),
      ),
    ];
  }

  Widget _note(String text, {bool error = false}) {
    final color = error ? AppTheme.alertRed : AppTheme.primaryGreen;
    return Container(
      margin: const EdgeInsets.only(bottom: 12),
      padding: const EdgeInsets.all(12),
      decoration: BoxDecoration(
        color: color.withValues(alpha: .08),
        borderRadius: BorderRadius.circular(12),
        border: Border.all(color: color.withValues(alpha: .25)),
      ),
      child: Row(crossAxisAlignment: CrossAxisAlignment.start, children: [
        Icon(error ? Icons.error_outline_rounded : Icons.check_circle_outline_rounded, size: 20, color: color),
        const SizedBox(width: 8),
        Expanded(child: AutoTranslatedText(text, style: TextStyle(fontSize: 14, color: error ? const Color(0xFF991B1B) : const Color(0xFF14532D), height: 1.35))),
      ]),
    );
  }

  Widget _roleTile(UserRole r, String label, String emoji) {
    final selected = _role == r;
    return Expanded(
      child: InkWell(
        onTap: () => setState(() => _role = r),
        borderRadius: BorderRadius.circular(14),
        child: AnimatedContainer(
          duration: const Duration(milliseconds: 160),
          padding: const EdgeInsets.symmetric(vertical: 12, horizontal: 4),
          decoration: BoxDecoration(
            color: selected ? AppTheme.primaryGreen.withValues(alpha: .08) : Colors.white,
            borderRadius: BorderRadius.circular(14),
            border: Border.all(color: selected ? AppTheme.primaryGreen : AppTheme.borderLight, width: selected ? 2 : 1),
          ),
          child: Column(children: [
            AutoTranslatedText(emoji, style: const TextStyle(fontSize: 26)),
            const SizedBox(height: 4),
            FittedBox(
              child: AutoTranslatedText(label,
                  style: TextStyle(fontSize: 14, fontWeight: FontWeight.w800, color: selected ? AppTheme.primaryGreen : AppTheme.textDark)),
            ),
          ]),
        ),
      ),
    );
  }

  Widget _field(TextEditingController c, String label, IconData icon, {TextInputAction? action}) => Padding(
        padding: const EdgeInsets.only(bottom: 10),
        child: TextField(controller: c, textInputAction: action, decoration: _dec(label, icon)),
      );

  InputDecoration _dec(String label, IconData icon) => InputDecoration(
        labelText: label,
        prefixIcon: Icon(icon, size: 21),
        filled: true,
        fillColor: Colors.white,
      );
}
