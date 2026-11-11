# Evaluation report

## Test set: held-out SMS messages

1035 messages (131 spam).

| Model | Accuracy | Precision | Recall | F1 | Missed spam | False alarms |
|---|---|---|---|---|---|---|
| Naive Bayes (ours) | 97.7% | 99.1% | 82.4% | 90.0% | 23 | 1 |
| Pretrained (mshenoda/roberta-spam) | 99.9% | 100.0% | 99.2% | 99.6% | 1 | 0 |

### Failure cases: Naive Bayes (ours) (24 total, most confident mistakes first)

| Kind | Message | Spam probability |
|---|---|---|
| missed spam | In The Simpsons Movie released in July 2007 name the band that died at the start of the film? A-Green Day, B-Blue Day, C-Red Day. (Send A, B or C) | 1.0% |
| missed spam | Babe: U want me dont u baby! Im nasty and have a thing 4 filthyguys. Fancy a rude time with a sexy bitch. How about we go slo n hard! Txt XXX SLO(4msgs) | 1.1% |
| missed spam | Xmas & New Years Eve tickets are now on sale from the club, during the day from 10am till 8pm, and on Thurs, Fri & Sat night this week. They're selling fast! | 3.3% |
| missed spam | Check Out Choose Your Babe Videos @ sms.shsex.netUN fgkslpoPW fgkslpo | 5.6% |
| missed spam | SMS. ac sun0819 posts HELLO:"You seem cool, wanted to say hi. HI!!!" Stop? Send STOP to 62468 | 7.4% |
| missed spam | Missed call alert. These numbers called but left no message. 07008009200 | 9.3% |
| missed spam | Burger King - Wanna play footy at a top stadium? Get 2 Burger King before 1st Sept and go Large or Super with Coca-Cola and walk out a winner | 14.2% |
| missed spam | Hi babe its Jordan, how r u? Im home from abroad and lonely, text me back if u wanna chat xxSP visionsms.com Text stop to stopCost 150p 08712400603 | 19.1% |
| missed spam | Want explicit SEX in 30 secs? Ring 02073162414 now! Costs 20p/min | 21.1% |
| missed spam | Would you like to see my XXX pics they are so hot they were nearly banned in the uk! | 21.5% |
| missed spam | FreeMsg Hey U, i just got 1 of these video/pic fones, reply WILD to this txt & ill send U my pics, hurry up Im so bored at work xxx (18 150p/rcvd STOP2stop) | 21.6% |
| missed spam | Latest News! Police station toilet stolen, cops have nothing to go on! | 24.0% |
| missed spam | ASKED 3MOBILE IF 0870 CHATLINES INCLU IN FREE MINS. INDIA CUST SERVs SED YES. L8ER GOT MEGA BILL. 3 DONT GIV A SHIT. BAILIFF DUE IN DAYS. I O £250 3 WANT £800 | 24.4% |
| missed spam | Thanks for the Vote. Now sing along with the stars with Karaoke on your mobile. For a FREE link just reply with SING now. | 27.0% |
| missed spam | ringtoneking 84484 | 28.0% |

### Failure cases: Pretrained (mshenoda/roberta-spam) (1 total, most confident mistakes first)

| Kind | Message | Spam probability |
|---|---|---|
| missed spam | Latest News! Police station toilet stolen, cops have nothing to go on! | 0.0% |

## Stress set: hand-written tricky messages

30 messages (15 spam).

| Model | Accuracy | Precision | Recall | F1 | Missed spam | False alarms |
|---|---|---|---|---|---|---|
| Naive Bayes (ours) | 63.3% | 100.0% | 26.7% | 42.1% | 11 | 0 |
| Pretrained (mshenoda/roberta-spam) | 93.3% | 88.2% | 100.0% | 93.8% | 0 | 2 |

### Failure cases: Naive Bayes (ours) (11 total, most confident mistakes first)

| Kind | Message | Spam probability |
|---|---|---|
| missed spam | Earn 5000 per day working from home. No experience needed. WhatsApp us now | 1.5% |
| missed spam | Hi dear, I am a lonely lady looking for a friend. Message me for photos | 1.8% |
| missed spam | Internship offer! Pay a 2000 registration fee to confirm your seat at a top company | 5.5% |
| missed spam | Your electricity will be disconnected tonight. Call 9876543210 immediately to avoid the cut | 9.9% |
| missed spam | Your parcel could not be delivered. Pay a small fee at http://track-parcel.info to reschedule | 12.8% |
| missed spam | Double your bitcoin in 24 hours. Guaranteed returns. Join our group today | 13.9% |
| missed spam | Limited offer: 90% discount on branded watches. Order now before stock runs out | 20.9% |
| missed spam | Final notice: your Netflix payment failed. Update your card details here to avoid cancellation | 23.0% |
| missed spam | URGENT! Your account is suspended, send your bank details to verify | 26.8% |
| missed spam | Dear customer, your KYC is expiring today. Update now at http://bank-kyc-update.in or your account will be blocked | 29.7% |
| missed spam | Get a pre-approved loan of 50000 with no documents. Reply YES to apply | 32.0% |

### Failure cases: Pretrained (mshenoda/roberta-spam) (2 total, most confident mistakes first)

| Kind | Message | Spam probability |
|---|---|---|
| false alarm | Your password was changed successfully. If this was not you, contact support through the official app | 100.0% |
| false alarm | Your account has been debited by Rs 450 at the canteen. Available balance is Rs 3200 | 100.0% |

## Caveats

- The stress set is small and hand-written. It shows where the models differ, not how they perform in general.
- The pretrained model's training data is not fully known to us, so it may have seen the SMS test messages. Treat its test-set scores as optimistic.
