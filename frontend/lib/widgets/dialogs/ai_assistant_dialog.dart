import '../auto_translated_text.dart';
import 'package:flutter/material.dart';
import 'package:provider/provider.dart';

import '../../core/theme/app_theme.dart';
import '../../core/voice/intent_parser.dart';
import '../../core/voice/voice_service.dart';
import '../../localization/l10n_extension.dart';
import '../../models/user_model.dart';
import '../../providers/auth_provider.dart';
import '../../providers/rescue_provider.dart';

const Map<String, Map<String, String>> _assistantPhrases = {
  'en': {
    'greeting': 'Namaste! Tell me what you need. For example: "I want to sell tomatoes" or "I need 100 kg onions near Pune".',
    'ask_crop': 'Which crop do you want to sell?',
    'ask_quantity': 'How many {} of {} do you want to sell?',
    'ask_price': 'What price per {} do you want?',
    'confirm': 'List {} {} of {} at ₹{} per {}?',
    'done': '✅ Crop Rescue listing created. Buyers can see it now.',
    'cancelled': 'Okay, cancelled. Tell me the correct details.',
    'searching': 'Showing {} for you.',
    'opening': 'Opening {}.',
    'login_needed': 'Please sign in as a farmer first.',
    'unknown': 'Sorry, I did not understand. Try: "Sell 500 kg tomato at 25 rupees".',
  },
  'hi': {
    'greeting': 'नमस्ते! बताइए क्या चाहिए। जैसे: "मुझे टमाटर बेचने हैं" या "पुणे में 100 किलो प्याज चाहिए"।',
    'ask_crop': 'आप कौन सी फसल बेचना चाहते हैं?',
    'ask_quantity': 'आपको कितने {} {} बेचने हैं?',
    'ask_price': 'प्रति {} कितना भाव चाहिए?',
    'confirm': '{} {} {} को ₹{} प्रति {} के भाव से बिक्री के लिए रखें?',
    'done': '✅ फसल बचाओ में सूची बन गई। खरीदार अब देख सकते हैं।',
    'cancelled': 'ठीक है, रद्द कर दिया। सही जानकारी बताइए।',
    'searching': 'आपके लिए {} दिखा रहे हैं।',
    'opening': '{} खोल रहे हैं।',
    'login_needed': 'कृपया पहले किसान के रूप में लॉगिन करें।',
    'unknown': 'माफ़ कीजिए, समझ नहीं आया। जैसे कहें: "500 किलो टमाटर 25 रुपये में बेचना है"।',
  },
  'mr': {
    'greeting': 'नमस्कार! काय हवं आहे सांगा. उदा: "मला टोमॅटो विकायचे आहेत" किंवा "पुण्यात 100 किलो कांदे हवेत".',
    'ask_crop': 'तुम्हाला कोणतं पीक विकायचं आहे?',
    'ask_quantity': 'किती {} {} विकायचे आहेत?',
    'ask_price': 'प्रति {} किती किंमत हवी आहे?',
    'confirm': '{} {} {} ₹{} प्रति {} या दराने विक्रीसाठी ठेवू का?',
    'done': '✅ पीक बचाव यादी तयार झाली. खरेदीदार आता बघू शकतात.',
    'cancelled': 'ठीक आहे, रद्द केलं. बरोबर माहिती सांगा.',
    'searching': 'तुमच्यासाठी {} दाखवत आहे.',
    'opening': '{} उघडत आहे.',
    'login_needed': 'कृपया आधी शेतकरी म्हणून लॉगिन करा.',
    'unknown': 'माफ करा, समजलं नाही. असं सांगा: "500 किलो टोमॅटो 25 रुपयांना विकायचे".',
  },
  'ta': {
    'greeting': 'வணக்கம்! உங்களுக்கு என்ன வேண்டும் சொல்லுங்கள். எ.கா: "தக்காளி விற்க வேண்டும்".',
    'ask_crop': 'எந்த பயிரை விற்க விரும்புகிறீர்கள்?',
    'ask_quantity': 'எத்தனை {} {} விற்க வேண்டும்?',
    'ask_price': 'ஒரு {} க்கு என்ன விலை வேண்டும்?',
    'confirm': '{} {} {} ஐ ஒரு {} க்கு ₹{} வீதம் பட்டியலிடலாமா?',
    'done': '✅ பயிர் மீட்பு பட்டியல் உருவாக்கப்பட்டது.',
    'cancelled': 'சரி, ரத்து செய்யப்பட்டது. சரியான விவரங்களை சொல்லுங்கள்.',
    'searching': 'உங்களுக்காக {} காட்டுகிறேன்.',
    'opening': '{} திறக்கிறேன்.',
    'login_needed': 'முதலில் விவசாயியாக உள்நுழையவும்.',
    'unknown': 'மன்னிக்கவும், புரியவில்லை. "500 கிலோ தக்காளி 25 ரூபாய்" என முயற்சிக்கவும்.',
  },
  'bn': {
    'greeting': 'নমস্কার! কী দরকার বলুন। যেমন: "টমেটো বিক্রি করতে চাই"।',
    'ask_crop': 'আপনি কোন ফসল বিক্রি করতে চান?',
    'ask_quantity': 'কত {} {} বিক্রি করতে চান?',
    'ask_price': 'প্রতি {} কত দাম চান?',
    'confirm': '{} {} {} ₹{} প্রতি {} দরে তালিকাভুক্ত করব?',
    'done': '✅ ফসল উদ্ধার তালিকা তৈরি হয়েছে।',
    'cancelled': 'ঠিক আছে, বাতিল করা হয়েছে। সঠিক তথ্য বলুন।',
    'searching': 'আপনার জন্য {} দেখাচ্ছি।',
    'opening': '{} খুলছি।',
    'login_needed': 'অনুগ্রহ করে আগে কৃষক হিসেবে লগইন করুন।',
    'unknown': 'দুঃখিত, বুঝতে পারিনি। বলুন: "৫০০ কেজি টমেটো ২৫ টাকায়"।',
  },
  'gu': {
    'greeting': 'નમસ્તે! શું જોઈએ છે કહો. જેમ કે: "મારે ટમેટા વેચવા છે".',
    'ask_crop': 'તમે કયો પાક વેચવા માંગો છો?',
    'ask_quantity': 'કેટલા {} {} વેચવા છે?',
    'ask_price': 'પ્રતિ {} કેટલો ભાવ જોઈએ?',
    'confirm': '{} {} {} ને ₹{} પ્રતિ {} ના ભાવે મૂકીએ?',
    'done': '✅ પાક બચાવ યાદી બની ગઈ. ખરીદદારો હવે જોઈ શકે છે.',
    'cancelled': 'ઠીક છે, રદ કર્યું. સાચી માહિતી કહો.',
    'searching': 'તમારા માટે {} બતાવી રહ્યો છું.',
    'opening': '{} ખોલી રહ્યો છું.',
    'login_needed': 'કૃપા કરીને પહેલા ખેડૂત તરીકે લૉગિન કરો.',
    'unknown': 'માફ કરશો, સમજાયું નહીં. કહો: "500 કિલો ટમેટા 25 રૂપિયા".',
  },
  'te': {
    'greeting': 'నమస్కారం! మీకు ఏమి కావాలో చెప్పండి. ఉదా: "నేను టమాటా అమ్మాలి".',
    'ask_crop': 'మీరు ఏ పంట అమ్మాలనుకుంటున్నారు?',
    'ask_quantity': 'ఎన్ని {} {} అమ్మాలి?',
    'ask_price': 'ఒక {} కి ఎంత ధర కావాలి?',
    'confirm': '{} {} {} ను ఒక {} కి ₹{} చొప్పున పెట్టాలా?',
    'done': '✅ పంట రక్షణ జాబితా సిద్ధమైంది.',
    'cancelled': 'సరే, రద్దు చేశాను. సరైన వివరాలు చెప్పండి.',
    'searching': 'మీ కోసం {} చూపిస్తున్నాను.',
    'opening': '{} తెరుస్తున్నాను.',
    'login_needed': 'దయచేసి ముందు రైతుగా లాగిన్ అవ్వండి.',
    'unknown': 'క్షమించండి, అర్థం కాలేదు. "500 కిలో టమాటా 25 రూపాయలు" అని చెప్పండి.',
  },
  'kn': {
    'greeting': 'ನಮಸ್ಕಾರ! ನಿಮಗೆ ಏನು ಬೇಕು ಹೇಳಿ. ಉದಾ: "ನಾನು ಟೊಮೇಟೊ ಮಾರಬೇಕು".',
    'ask_crop': 'ನೀವು ಯಾವ ಬೆಳೆ ಮಾರಲು ಬಯಸುತ್ತೀರಿ?',
    'ask_quantity': 'ಎಷ್ಟು {} {} ಮಾರಬೇಕು?',
    'ask_price': 'ಪ್ರತಿ {} ಗೆ ಎಷ್ಟು ಬೆಲೆ ಬೇಕು?',
    'confirm': '{} {} {} ಅನ್ನು ಪ್ರತಿ {} ಗೆ ₹{} ದರದಲ್ಲಿ ಹಾಕೋಣವೇ?',
    'done': '✅ ಬೆಳೆ ರಕ್ಷಣೆ ಪಟ್ಟಿ ಸಿದ್ಧವಾಗಿದೆ.',
    'cancelled': 'ಸರಿ, ರದ್ದುಪಡಿಸಲಾಗಿದೆ. ಸರಿಯಾದ ಮಾಹಿತಿ ಹೇಳಿ.',
    'searching': 'ನಿಮಗಾಗಿ {} ತೋರಿಸುತ್ತಿದ್ದೇನೆ.',
    'opening': '{} ತೆರೆಯುತ್ತಿದ್ದೇನೆ.',
    'login_needed': 'ದಯವಿಟ್ಟು ಮೊದಲು ರೈತರಾಗಿ ಲಾಗಿನ್ ಮಾಡಿ.',
    'unknown': 'ಕ್ಷಮಿಸಿ, ಅರ್ಥವಾಗಲಿಲ್ಲ. "500 ಕಿಲೋ ಟೊಮೇಟೊ 25 ರೂಪಾಯಿ" ಎಂದು ಹೇಳಿ.',
  },
};

String _phrase(String language, String key, [List<String> args = const []]) {
  final map = _assistantPhrases[language] ?? _assistantPhrases['en']!;
  var value = map[key] ?? _assistantPhrases['en']![key] ?? '';
  for (final arg in args) {
    value = value.replaceFirst('{}', arg);
  }
  return value;
}

class ChatMessage {
  final bool isUser;
  final String text;
  final List<String> chips;

  const ChatMessage({required this.isUser, required this.text, this.chips = const []});
}

enum _Stage { idle, awaitingCrop, awaitingQuantity, awaitingPrice, awaitingConfirm }

class AIAssistantDialog extends StatefulWidget {

  final void Function(String tabId)? onNavigate;

  const AIAssistantDialog({super.key, this.onNavigate});

  @override
  State<AIAssistantDialog> createState() => _AIAssistantDialogState();
}

class _AIAssistantDialogState extends State<AIAssistantDialog> {
  final _textController = TextEditingController();
  final _scrollController = ScrollController();
  final VoiceService _voice = PluginVoiceService();

  final List<ChatMessage> _messages = [];
  _Stage _stage = _Stage.idle;
  bool _isListening = false;

  CropTerm? _crop;
  double? _quantity;
  double? _price;
  String _unit = 'kg';

  String get _language => context.languageCode;

  @override
  void initState() {
    super.initState();
    WidgetsBinding.instance.addPostFrameCallback((_) {
      _say(_phrase(_language, 'greeting'));
    });
  }

  @override
  void dispose() {
    _textController.dispose();
    _scrollController.dispose();
    super.dispose();
  }

  void _say(String text, {List<String> chips = const []}) {
    if (!mounted) return;
    setState(() => _messages.add(ChatMessage(isUser: false, text: text, chips: chips)));
    _voice.speak(text, _language);
    _scrollToBottom();
  }

  void _scrollToBottom() {
    WidgetsBinding.instance.addPostFrameCallback((_) {
      if (_scrollController.hasClients) {
        _scrollController.animateTo(
          _scrollController.position.maxScrollExtent,
          duration: const Duration(milliseconds: 250),
          curve: Curves.easeOut,
        );
      }
    });
  }

  Future<void> _submit([String? preset]) async {
    final input = (preset ?? _textController.text).trim();
    if (input.isEmpty) return;

    setState(() {
      _messages.add(ChatMessage(isUser: true, text: input));
      _textController.clear();
    });
    _scrollToBottom();

    await Future<void>.delayed(const Duration(milliseconds: 350));
    if (!mounted) return;

    switch (_stage) {
      case _Stage.awaitingCrop:
        _handleCropAnswer(input);
        return;
      case _Stage.awaitingQuantity:
        _handleQuantityAnswer(input);
        return;
      case _Stage.awaitingPrice:
        _handlePriceAnswer(input);
        return;
      case _Stage.awaitingConfirm:
        _handleConfirmAnswer(input);
        return;
      case _Stage.idle:
        break;
    }

    _handleFreshUtterance(input);
  }

  void _handleFreshUtterance(String input) {
    final parsed = IntentParser.parse(input);

    switch (parsed.intent) {
      case AssistantIntent.sellCrop:
        _startSellFlow(parsed);
        return;

      case AssistantIntent.findCrop:
        _runSearch(parsed);
        return;

      case AssistantIntent.openRescue:
        _say(_phrase(_language, 'opening', [context.t('rescue')]));
        _navigate('rescue');
        return;

      case AssistantIntent.openOrders:
        _say(_phrase(_language, 'opening', [context.t('orders')]));
        _navigate('orders');
        return;

      case AssistantIntent.openWallet:
        _say(_phrase(_language, 'opening', [context.t('wallet')]));
        _navigate('wallet');
        return;

      case AssistantIntent.openCart:
        _say(_phrase(_language, 'opening', [context.t('cart')]));
        _navigate('cart');
        return;

      case AssistantIntent.openMarket:
        _say(_phrase(_language, 'opening', [context.t('market')]));
        _navigate('market');
        return;

      default:
        _say(_phrase(_language, 'unknown'));
    }
  }

  void _startSellFlow(ParsedUtterance parsed) {
    final auth = context.read<AuthProvider>();
    if (!auth.isLoggedIn || auth.user?.role != UserRole.farmer) {
      _say(_phrase(_language, 'login_needed'));
      return;
    }

    _crop = parsed.crop;
    _quantity = parsed.quantity;
    _price = parsed.price;
    _unit = parsed.unit ?? 'kg';

    _advanceSellFlow();
  }

  void _advanceSellFlow() {
    if (_crop == null) {
      _stage = _Stage.awaitingCrop;
      _say(_phrase(_language, 'ask_crop'), chips: ['🍅', '🧅', '🥔', '🍌']);
      return;
    }
    if (_quantity == null) {
      _stage = _Stage.awaitingQuantity;
      _say(_phrase(_language, 'ask_quantity', [_unit, _crop!.canonical]));
      return;
    }
    if (_price == null) {
      _stage = _Stage.awaitingPrice;
      _say(_phrase(_language, 'ask_price', [_unit]));
      return;
    }

    _stage = _Stage.awaitingConfirm;
    _say(
      _phrase(_language, 'confirm', [
        _quantity!.round().toString(),
        _unit,
        _crop!.canonical,
        _price!.round().toString(),
        _unit,
      ]),
      chips: ['✅ ${context.t('yes')}', '❌ ${context.t('no')}'],
    );
  }

  void _handleCropAnswer(String input) {
    final parsed = IntentParser.parse(input);
    if (parsed.crop == null) {
      _say(_phrase(_language, 'ask_crop'), chips: ['🍅', '🧅', '🥔', '🍌']);
      return;
    }
    _crop = parsed.crop;
    if (parsed.quantity != null) _quantity = parsed.quantity;
    if (parsed.price != null) _price = parsed.price;
    if (parsed.unit != null) _unit = parsed.unit!;
    _advanceSellFlow();
  }

  void _handleQuantityAnswer(String input) {
    final value = IntentParser.parseNumber(input);
    if (value == null) {
      _say(_phrase(_language, 'ask_quantity', [_unit, _crop!.canonical]));
      return;
    }
    final parsed = IntentParser.parse(input);
    if (parsed.unit != null) _unit = parsed.unit!;
    _quantity = value;
    _advanceSellFlow();
  }

  void _handlePriceAnswer(String input) {
    final value = IntentParser.parseNumber(input);
    if (value == null) {
      _say(_phrase(_language, 'ask_price', [_unit]));
      return;
    }
    _price = value;
    _advanceSellFlow();
  }

  Future<void> _handleConfirmAnswer(String input) async {
    if (IntentParser.isNegative(input)) {
      _resetSlots();
      _say(_phrase(_language, 'cancelled'));
      return;
    }
    if (!IntentParser.isAffirmative(input)) {
      _say(_phrase(_language, 'unknown'));
      return;
    }

    final auth = context.read<AuthProvider>();
    final rescue = context.read<RescueProvider>();
    final user = auth.user;

    final created = await rescue.publish(
      cropName: _crop!.canonical,
      category: _crop!.category,
      emoji: _crop!.emoji,
      quantity: _quantity!,
      unit: _unit,
      pricePerUnit: _price!,
      location: user?.address ?? '',
      sellBy: DateTime.now().add(const Duration(days: 3)),
      farmerId: user?.id ?? '',
      farmerName: user?.name ?? '',
    );

    if (!mounted) return;
    if (created == null) {
      _say(context.t('err_generic'));
      return;
    }

    _resetSlots();
    _say(_phrase(_language, 'done'));
  }

  void _resetSlots() {
    _stage = _Stage.idle;
    _crop = null;
    _quantity = null;
    _price = null;
    _unit = 'kg';
  }

  void _runSearch(ParsedUtterance parsed) {
    if (parsed.crop == null) {
      _say(_phrase(_language, 'unknown'));
      return;
    }
    context.read<RescueProvider>().setSearch(parsed.crop!.canonical);
    _say(_phrase(_language, 'searching', ['${parsed.crop!.emoji} ${parsed.crop!.canonical}']));
    _navigate('rescue');
  }

  void _navigate(String tabId) {
    final navigate = widget.onNavigate;
    if (navigate == null) return;
    Future<void>.delayed(const Duration(milliseconds: 700), () {
      if (!mounted) return;
      Navigator.of(context).pop();
      navigate(tabId);
    });
  }

  Future<void> _tapMic() async {
    if (!_voice.supportsSpeech) {

      ScaffoldMessenger.of(context).showSnackBar(
        const SnackBar(
          content: AutoTranslatedText('🎤 Microphone is not enabled in this build — type instead.'),
        ),
      );
      return;
    }

    setState(() => _isListening = true);
    final heard = await _voice.listen(_language);
    if (!mounted) return;
    setState(() => _isListening = false);
    if (heard != null && heard.trim().isNotEmpty) _submit(heard);
  }

  @override
  Widget build(BuildContext context) {
    return Dialog(
      insetPadding: const EdgeInsets.symmetric(horizontal: 16, vertical: 40),
      shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(24)),
      child: ConstrainedBox(
        constraints: BoxConstraints(
          maxWidth: 520,
          maxHeight: MediaQuery.of(context).size.height * 0.75,
        ),
        child: Column(
          mainAxisSize: MainAxisSize.min,
          children: [

            Container(
              padding: const EdgeInsets.fromLTRB(18, 14, 8, 14),
              decoration: const BoxDecoration(
                color: AppTheme.primaryGreen,
                borderRadius: BorderRadius.vertical(top: Radius.circular(24)),
              ),
              child: Row(
                children: [
                  AutoTranslatedText('🎤', style: TextStyle(fontSize: 22)),
                  const SizedBox(width: 10),
                  Expanded(
                    child: AutoTranslatedText(
                      context.t('ask_ai'),
                      style: const TextStyle(
                        fontSize: 16,
                        fontWeight: FontWeight.w900,
                        color: Colors.white,
                      ),
                    ),
                  ),
                  IconButton(
                    icon: const Icon(Icons.close, color: Colors.white),
                    onPressed: () => Navigator.of(context).pop(),
                  ),
                ],
              ),
            ),

            Flexible(
              child: ListView.builder(
                controller: _scrollController,
                padding: const EdgeInsets.all(16),
                itemCount: _messages.length,
                itemBuilder: (_, i) => _bubble(_messages[i]),
              ),
            ),

            if (_isListening)
              Padding(
                padding: const EdgeInsets.only(bottom: 8),
                child: AutoTranslatedText(
                  '🎤 ${context.t('voice_listening')}',
                  style: const TextStyle(
                    fontSize: 12,
                    fontWeight: FontWeight.w700,
                    color: AppTheme.primaryGreen,
                  ),
                ),
              ),

            Container(
              padding: const EdgeInsets.fromLTRB(12, 8, 12, 12),
              decoration: const BoxDecoration(
                border: Border(top: BorderSide(color: AppTheme.borderLight)),
              ),
              child: Row(
                children: [
                  Expanded(
                    child: TextField(
                      controller: _textController,
                      textInputAction: TextInputAction.send,
                      onSubmitted: (_) => _submit(),
                      decoration: InputDecoration(
                        hintText: context.t('voice_tap_to_speak'),
                        isDense: true,
                        contentPadding:
                            const EdgeInsets.symmetric(horizontal: 14, vertical: 12),
                      ),
                    ),
                  ),
                  const SizedBox(width: 8),
                  _circleButton(
                    icon: Icons.mic,
                    tooltip: context.t('voice_tap_to_speak'),
                    filled: _isListening,
                    onTap: _tapMic,
                  ),
                  const SizedBox(width: 6),
                  _circleButton(
                    icon: Icons.send,
                    tooltip: context.t('confirm'),
                    filled: true,
                    onTap: _submit,
                  ),
                ],
              ),
            ),
          ],
        ),
      ),
    );
  }

  Widget _bubble(ChatMessage message) {
    return Column(
      crossAxisAlignment:
          message.isUser ? CrossAxisAlignment.end : CrossAxisAlignment.start,
      children: [
        Container(
          margin: const EdgeInsets.only(bottom: 8),
          padding: const EdgeInsets.symmetric(horizontal: 14, vertical: 10),
          constraints: BoxConstraints(
            maxWidth: MediaQuery.of(context).size.width * 0.66,
          ),
          decoration: BoxDecoration(
            color: message.isUser ? AppTheme.primaryGreen : const Color(0xFFF3F4F6),
            borderRadius: BorderRadius.circular(16),
          ),
          child: AutoTranslatedText(
            message.text,
            style: TextStyle(
              fontSize: 13,
              height: 1.4,
              color: message.isUser ? Colors.white : AppTheme.textDark,
            ),
          ),
        ),
        if (message.chips.isNotEmpty)
          Padding(
            padding: const EdgeInsets.only(bottom: 10),
            child: Wrap(
              spacing: 8,
              children: message.chips
                  .map((chip) => ActionChip(
                        label: AutoTranslatedText(chip, style: const TextStyle(fontSize: 13)),
                        onPressed: () => _submit(_chipToUtterance(chip)),
                      ))
                  .toList(),
            ),
          ),
      ],
    );
  }

  String _chipToUtterance(String chip) {
    for (final term in cropVocabulary) {
      if (chip.contains(term.emoji)) return term.canonical;
    }
    if (chip.startsWith('✅')) return context.t('yes');
    if (chip.startsWith('❌')) return context.t('no');
    return chip;
  }

  Widget _circleButton({
    required IconData icon,
    required String tooltip,
    required bool filled,
    required VoidCallback onTap,
  }) {
    return Tooltip(
      message: tooltip,
      child: InkWell(
        onTap: onTap,
        borderRadius: BorderRadius.circular(22),
        child: Container(
          width: 42,
          height: 42,
          alignment: Alignment.center,
          decoration: BoxDecoration(
            color: filled ? AppTheme.primaryGreen : const Color(0xFFF3F4F6),
            shape: BoxShape.circle,
          ),
          child: Icon(
            icon,
            size: 20,
            color: filled ? Colors.white : AppTheme.textDark,
          ),
        ),
      ),
    );
  }
}
