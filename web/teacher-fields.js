// Additive teacher settings. Keep the existing Firestore profile schema and IDs.
export const TEACHER_DIRECTIONS=['Жаратылыстану-математикалық','Қоғамдық-гуманитарлық','Бастауыш білім','Өнер және шығармашылық','Дене тәрбиесі және қауіпсіздік','Пәнаралық зерттеу'];
export const TEACHER_SUBJECTS=[
  ['Информатика',0],['Математика',0],['Алгебра',0],['Геометрия',0],['Физика',0],['Химия',0],['Биология',0],['География',0],['Жаратылыстану',0],
  ['Қазақ тілі мен әдебиеті',1],['Қазақ тілі',1],['Қазақ әдебиеті',1],['Орыс тілі мен әдебиеті',1],['Орыс тілі',1],['Ағылшын тілі',1],['Қазақстан тарихы',1],['Дүниежүзі тарихы',1],['Құқық негіздері',1],
  ['Бастауыш сынып',2],['Көркем еңбек',3],['Музыка',3],['Дене шынықтыру',4],['Алғашқы әскери және технологиялық дайындық',4]
];
export function teacherDirectionForSubject(subject){const row=TEACHER_SUBJECTS.find(([s])=>s.toLocaleLowerCase('kk')===String(subject||'').trim().toLocaleLowerCase('kk'));return row?TEACHER_DIRECTIONS[row[1]]:''}
export function teacherProfileParts(profile={}){
  const bio=String(profile.bio||''),match=/^Зерттеу бағыты: ([^\n]+)\n\n/.exec(bio);
  // Existing free-form biographies are returned intact. Parse our known prefix only.
  if(match&&TEACHER_DIRECTIONS.includes(match[1]))return {...profile,direction:match[1],bio:bio.slice(match[0].length)};
  return {...profile,direction:TEACHER_DIRECTIONS.includes(profile.direction)?profile.direction:'',bio};
}
export function teacherStoredProfile(input={},required=false){
  const parts=teacherProfileParts(input);
  const subject=String(input.subject||'').trim(),direction=String(input.direction===undefined?parts.direction:input.direction||'').trim(),school=String(input.school||'').trim();
  const bio=String(parts.bio||'').trim();
  const error=message=>{throw Object.assign(Error(message),{status:400})};
  if(subject.length>80||school.length>120||bio.length>1000)error('Профиль өрістерінің көлемін тексеріңіз.');
  if(required&&!subject)error('Оқытатын пәніңізді таңдаңыз немесе енгізіңіз.');
  if(required&&!direction)error('Зерттеу бағытын таңдаңыз.');
  if(direction&&!TEACHER_DIRECTIONS.includes(direction))error('Зерттеу бағытын тізімнен таңдаңыз.');
  const storedBio=direction?'Зерттеу бағыты: '+direction+'\n\n'+bio:bio;
  if(storedBio.length>1000)error('Бағыт пен өзіңіз туралы мәтін бірге 1000 таңбадан аспауы керек.');
  return {school,grade:'',subject,bio:storedBio};
}
