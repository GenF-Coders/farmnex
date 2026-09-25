
enum AssistantIntent {
  sellCrop,
  findCrop,
  openRescue,
  openOrders,
  openWallet,
  openCart,
  openMarket,
  affirm,
  deny,
  unknown,
}

class CropTerm {
  final String canonical;
  final String emoji;
  final String category;
  final List<String> words;

  const CropTerm(this.canonical, this.emoji, this.category, this.words);
}

const List<CropTerm> cropVocabulary = [
  CropTerm('Tomato', '🍅', 'cat_vegetables', [
    'tomato', 'tomatoes', 'टमाटर', 'टोमॅटो', 'தக்காளி', 'টমেটো', 'ਟਮਾਟਰ', 'ટમેટા',
    'టమాటా', 'ಟೊಮೇಟೊ',
  ]),
  CropTerm('Onion', '🧅', 'cat_vegetables', [
    'onion', 'onions', 'प्याज', 'कांदा', 'कांदे', 'வெங்காயம்', 'পেঁয়াজ', 'ਪਿਆਜ਼',
    'ડુંગળી', 'ఉల్లి', 'ಈರುಳ್ಳಿ',
  ]),
  CropTerm('Potato', '🥔', 'cat_vegetables', [
    'potato', 'potatoes', 'आलू', 'बटाटा', 'உருளைக்கிழங்கு', 'আলু', 'ਆਲੂ', 'બટાકા',
    'బంగాళాదుంప', 'ಆಲೂಗಡ್ಡೆ',
  ]),
  CropTerm('Banana', '🍌', 'cat_fruits', [
    'banana', 'bananas', 'केला', 'केळी', 'வாழைப்பழம்', 'কলা', 'ਕੇਲਾ', 'કેળા',
    'అరటి', 'ಬಾಳೆಹಣ್ಣು',
  ]),
  CropTerm('Green Chilli', '🌶️', 'cat_vegetables', [
    'chilli', 'chili', 'mirchi', 'मिर्च', 'मिरची', 'மிளகாய்', 'লঙ্কা', 'ਮਿਰਚ', 'મરચાં',
    'మిరప', 'ಮೆಣಸಿನಕಾಯಿ',
  ]),
  CropTerm('Wheat', '🌾', 'cat_grains', [
    'wheat', 'गेहूं', 'गहू', 'கோதுமை', 'গম', 'ਕਣਕ', 'ઘઉં', 'గోధుమ', 'ಗೋಧಿ',
  ]),
  CropTerm('Soybean', '🌱', 'cat_grains', [
    'soybean', 'soya', 'सोयाबीन', 'சோயா', 'সয়াবিন', 'ਸੋਇਆਬੀਨ', 'સોયાબીન',
  ]),
  CropTerm('Grapes', '🍇', 'cat_fruits', [
    'grape', 'grapes', 'अंगूर', 'द्राक्ष', 'திராட்சை', 'আঙুর', 'ਅੰਗੂਰ', 'દ્રાક્ષ',
  ]),
];

const Map<String, String> _digitMap = {
  '०': '0', '१': '1', '२': '2', '३': '3', '४': '4',
  '५': '5', '६': '6', '७': '7', '८': '8', '९': '9',
  '௦': '0', '௧': '1', '௨': '2', '௩': '3', '௪': '4',
  '௫': '5', '௬': '6', '௭': '7', '௮': '8', '௯': '9',
  '০': '0', '১': '1', '২': '2', '৩': '3', '৪': '4',
  '৫': '5', '৬': '6', '৭': '7', '৮': '8', '৯': '9',
  '੦': '0', '੧': '1', '੨': '2', '੩': '3', '੪': '4',
  '੫': '5', '੬': '6', '੭': '7', '੮': '8', '੯': '9',
  '૦': '0', '૧': '1', '૨': '2', '૩': '3', '૪': '4',
  '૫': '5', '૬': '6', '૭': '7', '૮': '8', '૯': '9',
};

class ParsedUtterance {
  final AssistantIntent intent;
  final CropTerm? crop;
  final double? quantity;
  final String? unit;
  final double? price;
  final String? location;

  const ParsedUtterance({
    required this.intent,
    this.crop,
    this.quantity,
    this.unit,
    this.price,
    this.location,
  });
}

class IntentParser {
  const IntentParser._();

  static String _normalise(String input) {
    final buffer = StringBuffer();
    for (final ch in input.characters) {
      buffer.write(_digitMap[ch] ?? ch);
    }
    return buffer.toString().toLowerCase();
  }

  static bool _hasAny(String text, List<String> words) =>
      words.any((w) => text.contains(w.toLowerCase()));

  static const _sellWords = [
    'sell', 'selling', 'बेचना', 'बेचनी', 'बेचने', 'विकायचे', 'विकायचं', 'विकणे',
    'விற்க', 'বিক্রি', 'ਵੇਚਣ', 'ਵੇਚਣਾ', 'વેચવા', 'వి్క్రయ', 'ಮಾರಾಟ',
  ];
  static const _buyWords = [
    'buy', 'need', 'want', 'find', 'show', 'चाहिए', 'खरीदना', 'हवे', 'हवं', 'पाहिजे',
    'வேண்டும்', 'দরকার', 'ਚਾਹੀਦਾ', 'જોઈએ', 'కావాలి', 'ಬೇಕು',
  ];
  static const _rescueWords = [
    'rescue', 'बचाओ', 'बचाव', 'वाचवा', 'மீட்பு', 'উদ্ধার', 'ਬਚਾਓ', 'બચાવ',
  ];
  static const _orderWords = [
    'order', 'orders', 'ऑर्डर', 'ஆர்டர்', 'অর্ডার', 'ਆਰਡਰ', 'ઓર્ડર',
  ];
  static const _walletWords = [
    'wallet', 'balance', 'वॉलेट', 'बटुआ', 'பணப்பை', 'ওয়ালেট', 'ਬਟੂਆ', 'વૉલેટ',
  ];
  static const _cartWords = [
    'cart', 'basket', 'कार्ट', 'टोकरी', 'கூடை', 'কার্ট', 'ਟੋਕਰੀ', 'ટોપલી',
  ];
  static const _marketWords = [
    'market', 'mandi', 'मंडी', 'बाजार', 'மண்டி', 'বাজার', 'ਮੰਡੀ', 'મંડી',
  ];
  static const _yesWords = [
    'yes', 'yeah', 'ok', 'okay', 'haan', 'हाँ', 'हां', 'होय', 'ஆம்', 'হ্যাঁ',
    'ਹਾਂ', 'હા', 'అవును', 'ಹೌದು',
  ];
  static const _noWords = [
    'no', 'nahi', 'नहीं', 'नाही', 'இல்லை', 'না', 'ਨਹੀਂ', 'ના', 'కాదు', 'ಇಲ್ಲ',
  ];

  static const _priceWords = [
    'rupee', 'rupees', 'rs', '₹', 'रुपये', 'रुपए', 'रूपये', 'ரூபாய்', 'টাকা',
    'ਰੁਪਏ', 'રૂપિયા', 'రూపాయ', 'ರೂಪಾಯಿ', 'price', 'भाव', 'दर', 'किंमत',
  ];

  static const _kgWords = ['kg', 'kilo', 'किलो', 'கிலோ', 'কেজি', 'ਕਿਲੋ', 'કિલો'];
  static const _quintalWords = ['quintal', 'क्विंटल', 'क्विन्टल', 'ક્વિન્ટલ'];

  static ParsedUtterance parse(String raw) {
    final text = _normalise(raw);

    final crop = _findCrop(text);
    final numbers = _findNumbers(text);
    final unit = _hasAny(text, _quintalWords)
        ? 'Quintal'
        : (_hasAny(text, _kgWords) ? 'kg' : null);

    if (_hasAny(text, _rescueWords) && !_hasAny(text, _sellWords)) {
      return const ParsedUtterance(intent: AssistantIntent.openRescue);
    }
    if (_hasAny(text, _orderWords)) {
      return const ParsedUtterance(intent: AssistantIntent.openOrders);
    }
    if (_hasAny(text, _walletWords)) {
      return const ParsedUtterance(intent: AssistantIntent.openWallet);
    }
    if (_hasAny(text, _cartWords)) {
      return const ParsedUtterance(intent: AssistantIntent.openCart);
    }
    if (_hasAny(text, _marketWords) && crop == null) {
      return const ParsedUtterance(intent: AssistantIntent.openMarket);
    }

    if (_hasAny(text, _yesWords) && crop == null && numbers.isEmpty) {
      return const ParsedUtterance(intent: AssistantIntent.affirm);
    }
    if (_hasAny(text, _noWords) && crop == null && numbers.isEmpty) {
      return const ParsedUtterance(intent: AssistantIntent.deny);
    }

    final selling = _hasAny(text, _sellWords);
    final buying = _hasAny(text, _buyWords);

    double? quantity;
    double? price;
    if (numbers.isNotEmpty) {
      if (_hasAny(text, _priceWords) && numbers.length >= 2) {
        quantity = numbers[0];
        price = numbers[1];
      } else if (_hasAny(text, _priceWords)) {
        price = numbers[0];
      } else {
        quantity = numbers[0];
        if (numbers.length >= 2) price = numbers[1];
      }
    }

    final intent = selling
        ? AssistantIntent.sellCrop
        : (buying || crop != null ? AssistantIntent.findCrop : AssistantIntent.unknown);

    return ParsedUtterance(
      intent: intent,
      crop: crop,
      quantity: quantity,
      unit: unit,
      price: price,
      location: _findLocation(raw),
    );
  }

  static double? parseNumber(String raw) {
    final numbers = _findNumbers(_normalise(raw));
    return numbers.isEmpty ? null : numbers.first;
  }

  static bool isAffirmative(String raw) => _hasAny(_normalise(raw), _yesWords);

  static bool isNegative(String raw) => _hasAny(_normalise(raw), _noWords);

  static CropTerm? _findCrop(String text) {
    for (final term in cropVocabulary) {
      if (_hasAny(text, term.words)) return term;
    }
    return null;
  }

  static List<double> _findNumbers(String text) => RegExp(r'\d+(?:\.\d+)?')
      .allMatches(text)
      .map((m) => double.tryParse(m.group(0)!) ?? 0)
      .where((n) => n > 0)
      .toList();

  static String? _findLocation(String raw) {
    const cities = [
      'Pune', 'Nashik', 'Indore', 'Latur', 'Solapur', 'Jalgaon', 'Nagpur',
      'Mumbai', 'Bengaluru', 'Kolhapur', 'Aurangabad', 'Ludhiana', 'Amritsar',
      'Ahmedabad', 'Surat', 'Rajkot', 'Coimbatore', 'Madurai', 'Kolkata',
    ];
    final lower = raw.toLowerCase();
    for (final city in cities) {
      if (lower.contains(city.toLowerCase())) return city;
    }
    return null;
  }
}

extension _Chars on String {
  Iterable<String> get characters sync* {
    for (var i = 0; i < length; i++) {
      yield this[i];
    }
  }
}
