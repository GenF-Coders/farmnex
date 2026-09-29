import '../auto_translated_text.dart';
import 'package:flutter/material.dart';
import 'package:provider/provider.dart';
import '../../core/theme/app_theme.dart';
import '../../models/user_model.dart';
import '../../providers/auth_provider.dart';

class AuthDialog extends StatefulWidget {
  final String? reason;
  final UserRole initialRole;
  const AuthDialog({super.key, this.reason, this.initialRole = UserRole.farmer});
  @override State<AuthDialog> createState() => _AuthDialogState();
}

class _AuthDialogState extends State<AuthDialog> {
  bool _signup = false, _otpSent = false;
  UserRole _role = UserRole.farmer;
  final _mobile = TextEditingController(), _otp = TextEditingController(), _name = TextEditingController(), _surname = TextEditingController(), _dob = TextEditingController(), _address = TextEditingController(), _company = TextEditingController();
  String _gender = 'Male'; String? _status;

  @override void initState(){super.initState(); _role=widget.initialRole;}
  @override void dispose(){for(final c in [_mobile,_otp,_name,_surname,_dob,_address,_company]){c.dispose();} super.dispose();}

  Future<void> _otpRequest() async {
    final phone=_mobile.text.trim(); if(phone.replaceAll(RegExp(r'\D'),'').length<10){setState(()=>_status='Enter a valid mobile number.');return;}
    final a=context.read<AuthProvider>(); final ok=_signup?await a.requestRegistrationOtp(phone:phone):await a.requestLoginOtp(phone:phone);
    if(!mounted)return; setState(()=>_otpSent=ok); setState(()=>_status=ok?'OTP requested. Check your phone.':a.errorMessage);
  }

  Future<void> _verify() async {
    if(_otp.text.trim().length<4){setState(()=>_status='Enter the OTP.');return;}
    final a=context.read<AuthProvider>();
    if(_signup){
      final v=await a.verifyRegistrationOtp(otp:_otp.text.trim()); if(!v){if(mounted)setState(()=>_status=a.errorMessage);return;}
      final ok=await a.completeRegistration(role:_role);
      if(ok){await a.updateMyProfile(name:'${_name.text.trim()} ${_surname.text.trim()}'.trim(),surname:_surname.text.trim(),dateOfBirth:_dob.text.trim(),gender:_gender,address:_address.text.trim(),companyName:_company.text.trim().isEmpty?null:_company.text.trim());}
      if(!mounted)return; if(ok)Navigator.of(context).pop(true); else setState(()=>_status=a.errorMessage);
    }else{
      final ok=await a.verifyLoginOtp(otp:_otp.text.trim()); if(!mounted)return; if(ok)Navigator.of(context).pop(true); else setState(()=>_status=a.errorMessage);
    }
  }

  @override Widget build(BuildContext context){
    final a=context.watch<AuthProvider>();
    return Dialog(
      backgroundColor: const Color(0xFFF7F6F2), insetPadding: const EdgeInsets.symmetric(horizontal: 16,vertical: 22), shape:RoundedRectangleBorder(borderRadius:BorderRadius.circular(20)),
      child: ConstrainedBox(constraints: const BoxConstraints(maxWidth:411,maxHeight:820), child: SingleChildScrollView(padding: const EdgeInsets.fromLTRB(24,22,24,24), child: Column(crossAxisAlignment:CrossAxisAlignment.stretch,children:[
        Row(children:[const Expanded(child:AutoTranslatedText('FarmNex',style:TextStyle(fontSize:21,fontWeight:FontWeight.w900,color:AppTheme.primaryGreen))),IconButton(onPressed:()=>Navigator.pop(context),icon:const Icon(Icons.close_rounded))]),
        AutoTranslatedText('Better markets, smarter farming, brighter futures.',style:TextStyle(fontSize:12,color:AppTheme.textMuted)), const SizedBox(height:20),
        Container(padding:const EdgeInsets.all(4),decoration:BoxDecoration(color:const Color(0xFFEFEFEA),borderRadius:BorderRadius.circular(11)),child:Row(children:[Expanded(child:_mode('Login',!_signup)),Expanded(child:_mode('Register',_signup))])),
        const SizedBox(height:18),
        if(widget.reason!=null)Padding(padding:const EdgeInsets.only(bottom:10),child:AutoTranslatedText(widget.reason!,style:const TextStyle(fontSize:11,color:AppTheme.textMuted))),
        if(_signup)...[
          AutoTranslatedText('Select account role',style:TextStyle(fontSize:11,fontWeight:FontWeight.w800,color:AppTheme.textMuted)),const SizedBox(height:8),
          Row(children:[_roleTile(UserRole.farmer,'Farmer','🌾'),const SizedBox(width:7),_roleTile(UserRole.buyer,'Buyer','🏢'),const SizedBox(width:7),_roleTile(UserRole.logistics,'Logistics','🚚'),const SizedBox(width:7),_roleTile(UserRole.admin,'Admin','🛡️')]),const SizedBox(height:12),
          _field(_name,'Name',Icons.person_outline),_field(_surname,'Surname',Icons.badge_outlined),
          TextField(controller:_dob,readOnly:true,decoration:_dec('Date of birth',Icons.calendar_today_outlined),onTap:()async{final d=await showDatePicker(context:context,firstDate:DateTime(1940),lastDate:DateTime.now(),initialDate:DateTime(2000));if(d!=null)_dob.text='${d.year.toString().padLeft(4,'0')}-${d.month.toString().padLeft(2,'0')}-${d.day.toString().padLeft(2,'0')}';}),
          const SizedBox(height:9),DropdownButtonFormField<String>(value:_gender,decoration:_dec('Gender',Icons.person_outline),items:const[DropdownMenuItem(value:'Male',child:AutoTranslatedText('Male')),DropdownMenuItem(value:'Female',child:AutoTranslatedText('Female')),DropdownMenuItem(value:'Other',child:AutoTranslatedText('Other'))],onChanged:(v)=>setState(()=>_gender=v??_gender)),const SizedBox(height:9),
          _field(_address,'Address',Icons.location_on_outlined),if(_role!=UserRole.farmer)_field(_company,_role==UserRole.logistics?'Firm / vehicle details':'Company name',Icons.business_outlined),
        ],
        _field(_mobile,'Mobile number',Icons.phone_outlined,keyboard:TextInputType.phone),
        if(_otpSent)...[const SizedBox(height:9),_field(_otp,'OTP',Icons.lock_clock_outlined,keyboard:TextInputType.number)],
        const SizedBox(height:12),if(_status!=null)Padding(padding:const EdgeInsets.only(bottom:10),child:AutoTranslatedText(_status!,textAlign:TextAlign.center,style:const TextStyle(fontSize:11,fontWeight:FontWeight.w700,color:AppTheme.primaryGreen))),
        SizedBox(height:48,child:ElevatedButton(onPressed:a.isLoading?null:(_otpSent?_verify:_otpRequest),child:a.isLoading?const SizedBox(width:20,height:20,child:CircularProgressIndicator(strokeWidth:2,color:Colors.white)):AutoTranslatedText(_otpSent?'Verify OTP':'Send OTP'))),
        const SizedBox(height:8),AutoTranslatedText('OTP verification is required for account access.',textAlign:TextAlign.center,style:TextStyle(fontSize:9.5,color:AppTheme.textMuted)),
      ]))),
    );
  }

  Widget _mode(String text,bool selected)=>InkWell(onTap:()=>setState((){_signup=text=='Register';_otpSent=false;_otp.clear();_status=null;}),borderRadius:BorderRadius.circular(9),child:Container(padding:const EdgeInsets.symmetric(vertical:9),decoration:BoxDecoration(color:selected?Colors.white:Colors.transparent,borderRadius:BorderRadius.circular(9)),alignment:Alignment.center,child:AutoTranslatedText(text,style:TextStyle(fontSize:12.5,fontWeight:selected?FontWeight.w800:FontWeight.w500,color:selected?AppTheme.primaryGreen:AppTheme.textMuted))));
  Widget _roleTile(UserRole r,String label,String emoji)=>Expanded(child:InkWell(onTap:()=>setState(()=>_role=r),borderRadius:BorderRadius.circular(10),child:Container(padding:const EdgeInsets.symmetric(vertical:8,horizontal:2),decoration:BoxDecoration(color:_role==r?AppTheme.primaryGreen.withValues(alpha:.08):Colors.white,borderRadius:BorderRadius.circular(10),border:Border.all(color:_role==r?AppTheme.primaryGreen:AppTheme.borderLight,width:_role==r?1.5:1)),child:Column(children:[AutoTranslatedText(emoji,style:const TextStyle(fontSize:18)),const SizedBox(height:2),FittedBox(child:AutoTranslatedText(label,style:TextStyle(fontSize:9,fontWeight:FontWeight.w800,color:_role==r?AppTheme.primaryGreen:AppTheme.textDark))) ]))));
  Widget _field(TextEditingController c,String label,IconData icon,{TextInputType? keyboard})=>Padding(padding:const EdgeInsets.only(bottom:9),child:TextField(controller:c,keyboardType:keyboard,decoration:_dec(label,icon)));
  InputDecoration _dec(String label,IconData icon)=>InputDecoration(labelText:label,prefixIcon:Icon(icon,size:19),filled:true,fillColor:Colors.white,border:OutlineInputBorder(borderRadius:BorderRadius.circular(11),borderSide:const BorderSide(color:AppTheme.borderLight)),enabledBorder:OutlineInputBorder(borderRadius:BorderRadius.circular(11),borderSide:const BorderSide(color:AppTheme.borderLight)),contentPadding:const EdgeInsets.symmetric(horizontal:12,vertical:13));
}
