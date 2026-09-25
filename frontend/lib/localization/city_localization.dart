
class LocalizedCity {
  const LocalizedCity._();

  static const List<String> maharashtraCities = [
    'Pune', 'Mumbai', 'Navi Mumbai', 'Thane', 'Nashik', 'Nagpur',
    'Aurangabad', 'Kolhapur', 'Solapur', 'Sangli', 'Satara', 'Ahmednagar',
    'Latur', 'Nanded', 'Amravati', 'Akola', 'Jalgaon', 'Dhule', 'Raigad',
    'Ratnagiri', 'Sindhudurg',
  ];

  static const Map<String, Map<String, String>> _names = {
    'hi': {
      'All Maharashtra': 'पूरा महाराष्ट्र', 'Pune': 'पुणे', 'Mumbai': 'मुंबई',
      'Navi Mumbai': 'नवी मुंबई', 'Thane': 'ठाणे', 'Nashik': 'नासिक',
      'Nagpur': 'नागपुर', 'Aurangabad': 'औरंगाबाद', 'Kolhapur': 'कोल्हापुर',
      'Solapur': 'सोलापुर', 'Sangli': 'सांगली', 'Satara': 'सातारा',
      'Ahmednagar': 'अहमदनगर', 'Latur': 'लातूर', 'Nanded': 'नांदेड',
      'Amravati': 'अमरावती', 'Akola': 'अकोला', 'Jalgaon': 'जलगांव',
      'Dhule': 'धुले', 'Raigad': 'रायगढ़', 'Ratnagiri': 'रत्नागिरी',
      'Sindhudurg': 'सिंधुदुर्ग',
    },
    'mr': {
      'All Maharashtra': 'संपूर्ण महाराष्ट्र', 'Pune': 'पुणे', 'Mumbai': 'मुंबई',
      'Navi Mumbai': 'नवी मुंबई', 'Thane': 'ठाणे', 'Nashik': 'नाशिक',
      'Nagpur': 'नागपूर', 'Aurangabad': 'औरंगाबाद', 'Kolhapur': 'कोल्हापूर',
      'Solapur': 'सोलापूर', 'Sangli': 'सांगली', 'Satara': 'सातारा',
      'Ahmednagar': 'अहमदनगर', 'Latur': 'लातूर', 'Nanded': 'नांदेड',
      'Amravati': 'अमरावती', 'Akola': 'अकोला', 'Jalgaon': 'जळगाव',
      'Dhule': 'धुळे', 'Raigad': 'रायगड', 'Ratnagiri': 'रत्नागिरी',
      'Sindhudurg': 'सिंधुदुर्ग',
    },
    'te': {
      'All Maharashtra': 'మొత్తం మహారాష్ట్ర', 'Pune': 'పుణే', 'Mumbai': 'ముంబై',
      'Navi Mumbai': 'నవి ముంబై', 'Thane': 'థానే', 'Nashik': 'నాసిక్',
      'Nagpur': 'నాగ్‌పూర్', 'Aurangabad': 'ఔరంగాబాద్', 'Kolhapur': 'కొల్హాపూర్',
      'Solapur': 'సోలాపూర్', 'Sangli': 'సాంగ్లీ', 'Satara': 'సతారా',
      'Ahmednagar': 'అహ్మద్‌నగర్', 'Latur': 'లాతూర్', 'Nanded': 'నాందేడ్',
      'Amravati': 'అమరావతి', 'Akola': 'అకోలా', 'Jalgaon': 'జల్గావ్',
      'Dhule': 'ధులే', 'Raigad': 'రాయగఢ్', 'Ratnagiri': 'రత్నగిరి',
      'Sindhudurg': 'సింధుదుర్గ్',
    },
    'ta': {
      'All Maharashtra': 'மகாராஷ்டிரா முழுவதும்', 'Pune': 'புனே', 'Mumbai': 'மும்பை',
      'Navi Mumbai': 'நவி மும்பை', 'Thane': 'தானே', 'Nashik': 'நாசிக்',
      'Nagpur': 'நாக்பூர்', 'Aurangabad': 'அவுரங்காபாத்', 'Kolhapur': 'கோலாப்பூர்',
      'Solapur': 'சோலாப்பூர்', 'Sangli': 'சாங்க்லி', 'Satara': 'சதாரா',
      'Ahmednagar': 'அகமதுநகர்', 'Latur': 'லாத்தூர்', 'Nanded': 'நாந்தேட்',
      'Amravati': 'அமராவதி', 'Akola': 'அகோலா', 'Jalgaon': 'ஜல்கான்',
      'Dhule': 'துலே', 'Raigad': 'ராய்கட்', 'Ratnagiri': 'ரத்னகிரி',
      'Sindhudurg': 'சிந்துதுர்க்',
    },
    'kn': {
      'All Maharashtra': 'ಮಹಾರಾಷ್ಟ್ರದಾದ್ಯಂತ', 'Pune': 'ಪುಣೆ', 'Mumbai': 'ಮುಂಬೈ',
      'Navi Mumbai': 'ನವಿ ಮುಂಬೈ', 'Thane': 'ಥಾಣೆ', 'Nashik': 'ನಾಸಿಕ್',
      'Nagpur': 'ನಾಗಪುರ', 'Aurangabad': 'ಔರಂಗಾಬಾದ್', 'Kolhapur': 'ಕೊಲ್ಹಾಪುರ',
      'Solapur': 'ಸೊಲಾಪುರ', 'Sangli': 'ಸಾಂಗ್ಲಿ', 'Satara': 'ಸಾತಾರಾ',
      'Ahmednagar': 'ಅಹಮದ್‌ನಗರ', 'Latur': 'ಲಾತೂರ್', 'Nanded': 'ನಾಂದೇಡ್',
      'Amravati': 'ಅಮರಾವತಿ', 'Akola': 'ಅಕೋಲಾ', 'Jalgaon': 'ಜಲಗಾಂವ್',
      'Dhule': 'ಧುಳೆ', 'Raigad': 'ರಾಯಗಢ', 'Ratnagiri': 'ರತ್ನಗಿರಿ',
      'Sindhudurg': 'ಸಿಂಧುದುರ್ಗ',
    },
    'bn': {
      'All Maharashtra': 'সমগ্র মহারাষ্ট্র', 'Pune': 'পুনে', 'Mumbai': 'মুম্বাই',
      'Navi Mumbai': 'নবি মুম্বাই', 'Thane': 'থানে', 'Nashik': 'নাসিক',
      'Nagpur': 'নাগপুর', 'Aurangabad': 'ঔরঙ্গাবাদ', 'Kolhapur': 'কোলহাপুর',
      'Solapur': 'সোলাপুর', 'Sangli': 'সাংলি', 'Satara': 'সাতারা',
      'Ahmednagar': 'আহমেদনগর', 'Latur': 'লাতুর', 'Nanded': 'নান্দেড়',
      'Amravati': 'অমরাবতী', 'Akola': 'আকোলা', 'Jalgaon': 'জলগাঁও',
      'Dhule': 'ধুলে', 'Raigad': 'রায়গড়', 'Ratnagiri': 'রত্নাগিরি',
      'Sindhudurg': 'সিন্ধুদুর্গ',
    },
    'gu': {
      'All Maharashtra': 'સમગ્ર મહારાષ્ટ્ર', 'Pune': 'પુણે', 'Mumbai': 'મુંબઈ',
      'Navi Mumbai': 'નવી મુંબઈ', 'Thane': 'થાણે', 'Nashik': 'નાશિક',
      'Nagpur': 'નાગપુર', 'Aurangabad': 'ઔરંગાબાદ', 'Kolhapur': 'કોલ્હાપુર',
      'Solapur': 'સોલાપુર', 'Sangli': 'સાંગલી', 'Satara': 'સાતારા',
      'Ahmednagar': 'અહમદનગર', 'Latur': 'લાતુર', 'Nanded': 'નાંદેડ',
      'Amravati': 'અમરાવતી', 'Akola': 'અકોલા', 'Jalgaon': 'જલગાંવ',
      'Dhule': 'ધુલે', 'Raigad': 'રાયગઢ', 'Ratnagiri': 'રત્નાગિરી',
      'Sindhudurg': 'સિંધુદુર્ગ',
    },
  };

  static String name(String city, String languageCode) {
    return _names[languageCode]?[city] ?? city;
  }
}
