import {test} from 'node:test';
import assert from 'node:assert/strict';
import {teacherDirectionForSubject,teacherProfileParts,teacherStoredProfile} from '../web/teacher-fields.js';

test('legacy teacher biography is preserved and a stored direction survives a round trip',()=>{
 const old={school:'Мектеп',grade:'',subject:'Биология',bio:'Бұрын жазылған мәтін\nЕкінші жол'};
 assert.equal(teacherProfileParts(old).bio,old.bio);
 const stored=teacherStoredProfile({...old,direction:'Жаратылыстану-математикалық'});
 assert.deepEqual(Object.keys(stored).sort(),['bio','grade','school','subject']);
 const decoded=teacherProfileParts(stored);assert.equal(decoded.bio,old.bio);assert.equal(decoded.direction,'Жаратылыстану-математикалық');
 assert.deepEqual(teacherStoredProfile(stored),stored);
 assert.equal(teacherProfileParts({bio:'Зерттеу бағыты: бұрынғы еркін атау\n\nМәтін'}).bio,'Зерттеу бағыты: бұрынғы еркін атау\n\nМәтін');
});

test('subject suggestions support other disciplines and custom subjects require the teacher choice',()=>{
 assert.equal(teacherDirectionForSubject('Қазақ тілі мен әдебиеті'),'Қоғамдық-гуманитарлық');
 assert.equal(teacherDirectionForSubject('Физика'),'Жаратылыстану-математикалық');
 assert.equal(teacherDirectionForSubject('Бастауыш сынып'),'Бастауыш білім');
 assert.equal(teacherDirectionForSubject('Робототехника элективі'),'');
 assert.equal(teacherStoredProfile({subject:'Робототехника элективі',direction:'Пәнаралық зерттеу'},true).subject,'Робототехника элективі');
 assert.throws(()=>teacherStoredProfile({subject:'Физика',direction:'Пәнаралық зерттеу',bio:'x'.repeat(1000)}),/1000/);
});
