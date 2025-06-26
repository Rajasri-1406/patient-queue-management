-- ? Create Table
CREATE TABLE PATIENT_TRIAGE (
    PATIENT_ID VARCHAR2(10) PRIMARY KEY,          -- Auto-generated: 'P001', 'P002', etc.
    NAME VARCHAR2(100) NOT NULL,                  -- Patient's name
    AGE NUMBER NOT NULL,                          -- Patient's age
    GENDER VARCHAR2(10) NOT NULL,                 -- Gender (Male/Female/Other)
    CONTACT NUMBER(15) NOT NULL,                  -- Contact number
    SYMPTOMS CLOB NOT NULL,                       -- Symptoms description
    MEDICAL_HISTORY CLOB,                         -- Optional history
    TRIAGE_LEVEL VARCHAR2(50),                    -- Critical / High / Moderate / Low
    ESTIMATED_WAITING_TIME VARCHAR2(50),          -- eg: '15 mins'
    APPOINTMENT_DATE DATE NOT NULL,               -- Assigned date
    STATUS VARCHAR2(20) DEFAULT 'Pending',        -- Pending / Diagnosed / Cancelled
    ASSIGNED_DOCTOR VARCHAR2(100),                -- Doctor user ID
    BOOKING_TIME TIMESTAMP,                       -- Exact booking time (renamed from BOOKING_DATE/TIME)
    BP VARCHAR2(20),                              -- Blood Pressure
    HEART_RATE NUMBER,                            -- Heart Rate
    RESPIRATORY_RATE NUMBER,                      -- Breathing rate
    OXYGEN_SATURATION NUMBER,                     -- SpO2 value
    SPECIALIZATION VARCHAR2(50),                  -- Cardiology, Neurology etc.
    APPOINTMENT_TIME VARCHAR2(20),                -- eg: '10:30 AM'
    BOOKING_DATETIME TIMESTAMP DEFAULT CURRENT_TIMESTAMP  -- Time of appointment booking
);



-- ? Create Trigger to Format PATIENT_ID as 'P001', 'P002', etc.
CREATE OR REPLACE TRIGGER PATIENT_ID_TRIGGER
BEFORE INSERT ON PATIENT_TRIAGE
FOR EACH ROW
BEGIN
    SELECT 'P' || LPAD(PATIENT_SEQ.NEXTVAL, 3, '0') INTO :NEW.PATIENT_ID FROM DUAL;
END;
/

desc patient_triage;

--------------------------------------------------------------------------------
CREATE TABLE USERS1 (
    USER_ID VARCHAR2(50) PRIMARY KEY,
    NAME VARCHAR2(100),
    ROLE VARCHAR2(50) NOT NULL CHECK (ROLE IN ('Doctor', 'Patient', 'Admin')),
    PASSWORD VARCHAR2(255) NOT NULL
);


insert into users1 values('D01','Cdoc','Doctor','cd01','Cardiology');
insert into users1 values('D02','Ndoc','Doctor','nd02','Neurology');
insert into users1 values('D03','Pdoc','Doctor','pd03','Pediatrics');
insert into users1 values('D04','Odoc','Doctor','od04','Orthopedics');
insert into users1 values('D05','Gdoc','Doctor','gd05','General Medicine');
insert into users1 values('D10','Cdoc1','Doctor','cd10','Cardiology');




CREATE OR REPLACE TRIGGER PATIENT_ID_TRIGGER
BEFORE INSERT ON PATIENT_TRIAGE
FOR EACH ROW
BEGIN
    SELECT 'P' || LPAD(PATIENT_SEQ.NEXTVAL, 3, '0') INTO :NEW.PATIENT_ID FROM DUAL;
END;
/


--------------------------------------------
CREATE TABLE walkins (
    token_no NUMBER,
    patient_name VARCHAR2(100),
    age NUMBER,
    gender VARCHAR2(10),
    symptoms CLOB,
    room_no VARCHAR2(10),
    doctor_name VARCHAR2(50),
    specialization VARCHAR2(50),
    visit_date DATE
);

INSERT INTO walkins (token_no, patient_name, age, gender, symptoms, room_no, doctor_name, specialization, visit_date)
VALUES (1, 'John Doe', 45, 'Male', 'Chest Pain', '101', 'WCdoc', 'Cardiology', TO_DATE('2025-04-27', 'YYYY-MM-DD'));

INSERT INTO walkins (token_no, patient_name, age, gender, symptoms, room_no, doctor_name, specialization, visit_date)
VALUES (2, 'Jane Smith', 52, 'Female', 'Shortness of Breath', '102', 'WCdoc', 'Cardiology', TO_DATE('2025-04-27', 'YYYY-MM-DD'));

INSERT INTO walkins (token_no, patient_name, age, gender, symptoms, room_no, doctor_name, specialization, visit_date)
VALUES (3, 'Bob Brown', 60, 'Male', 'Heart Palpitations', '103', 'WCdoc', 'Cardiology', TO_DATE('2025-04-27', 'YYYY-MM-DD'));

INSERT INTO walkins (token_no, patient_name, age, gender, symptoms, room_no, doctor_name, specialization, visit_date)
VALUES (1, 'Alice Green', 30, 'Female', 'Fever and Cough', '201', 'WGdoc', 'General Medicine', TO_DATE('2025-04-27', 'YYYY-MM-DD'));

INSERT INTO walkins (token_no, patient_name, age, gender, symptoms, room_no, doctor_name, specialization, visit_date)
VALUES (2, 'Tom White', 40, 'Male', 'Body Ache', '202', 'WGdoc', 'General Medicine', TO_DATE('2025-04-27', 'YYYY-MM-DD'));

INSERT INTO walkins (token_no, patient_name, age, gender, symptoms, room_no, doctor_name, specialization, visit_date)
VALUES (1, 'Sara Blue', 5, 'Female', 'High Fever', '301', 'WPdoc', 'Pediatrics', TO_DATE('2025-04-27', 'YYYY-MM-DD'));

INSERT INTO walkins (token_no, patient_name, age, gender, symptoms, room_no, doctor_name, specialization, visit_date)
VALUES (2, 'Mike Yellow', 8, 'Male', 'Stomach Ache', '302', 'WPdoc', 'Pediatrics', TO_DATE('2025-04-27', 'YYYY-MM-DD'));


-------------------------------------------

CREATE TABLE PPD (
    PATIENT_ID VARCHAR2(10),
    PATIENT_NAME VARCHAR2(100),
    DOCTOR_ID VARCHAR2(10),
    DOCTOR_NAME VARCHAR2(100),
    SPECIALIZATION VARCHAR2(50),
    CRITICALITY VARCHAR2(20),
    APPOINTMENT_DATE DATE,
    APPOINTMENT_TIME VARCHAR2(10),
    PRESCRIBED_MEDICINES VARCHAR2(500),
    PRESCRIPTION_DETAILS VARCHAR2(1000),
    ADDITIONAL_NOTES VARCHAR2(1000)
);
drop table ppd;
select * from ppd;
----------------------------------

CREATE SEQUENCE emergency_cases_seq
    START WITH 1
    INCREMENT BY 1
    NOCACHE
    NOCYCLE;
drop SEQUENCE emergency_cases_seq;
-- EMERGENCY CASES Table
CREATE TABLE emergency_cases (
    id NUMBER PRIMARY KEY,
    guardian_name VARCHAR2(100) NOT NULL,
    phone VARCHAR2(15) NOT NULL,
    location VARCHAR2(200) NOT NULL
);
select * from emergency_cases;

-- TRIGGER to Auto-increment ID in EMERGENCY_CASES table
CREATE OR REPLACE TRIGGER emergency_cases_trigger
BEFORE INSERT ON emergency_cases
FOR EACH ROW
BEGIN
    SELECT emergency_cases_seq.NEXTVAL INTO :NEW.id FROM dual;
END;
/
----------------------------------------------------------
-- ? Create Sequence for Primary Key
CREATE SEQUENCE doctor_schedule_seq START WITH 1 INCREMENT BY 1;
drop SEQUENCE doctor_schedule_seq;
-- ? Create Table
CREATE TABLE DOCTOR_SCHEDULE (
    DOCTOR_ID VARCHAR2(20),
    DOCTOR_NAME VARCHAR2(100),
    SPECIALIZATION VARCHAR2(50),
    AVAILABLE_DAYS VARCHAR2(50),  -- e.g., "Monday, Wednesday"
    FOREIGN KEY (DOCTOR_ID) REFERENCES USERS1(USER_ID)
);

-- ? Insert Cardiologist Availability
INSERT INTO DOCTOR_SCHEDULE (DOCTOR_ID, DOCTOR_NAME, SPECIALIZATION, AVAILABLE_DAYS)
VALUES ('D01', 'Cdoc', 'Cardiology', 'Monday, Wednesday');

INSERT INTO DOCTOR_SCHEDULE (DOCTOR_ID, DOCTOR_NAME, SPECIALIZATION, AVAILABLE_DAYS)
VALUES ('D10', 'Cdoc1', 'Cardiology', 'Tuesday, Thursday');

INSERT INTO DOCTOR_SCHEDULE (DOCTOR_ID, DOCTOR_NAME, SPECIALIZATION, AVAILABLE_DAYS)
VALUES ('D03', 'Pdoc', 'Pediatrics', 'Monday, Tuesday');

INSERT INTO DOCTOR_SCHEDULE (DOCTOR_ID, DOCTOR_NAME, SPECIALIZATION, AVAILABLE_DAYS)
VALUES ('D13', 'Pdoc1', 'Pediatrics', 'Wednesday, Thursday');

INSERT INTO DOCTOR_SCHEDULE (DOCTOR_ID, DOCTOR_NAME, SPECIALIZATION, AVAILABLE_DAYS)
VALUES ('D04', 'Odoc', 'Orthopedics', 'Tuesday, Wednesday');


INSERT INTO DOCTOR_SCHEDULE (DOCTOR_ID, DOCTOR_NAME, SPECIALIZATION, AVAILABLE_DAYS)
VALUES ('D02', 'Ndoc', 'Neurology', 'Wednesday, Thursday');
INSERT INTO DOCTOR_SCHEDULE (DOCTOR_ID, DOCTOR_NAME, SPECIALIZATION, AVAILABLE_DAYS)
VALUES ('D11', 'Ndoc1', 'Neurology', 'Monday, Tuesday');

INSERT INTO DOCTOR_SCHEDULE (DOCTOR_ID, DOCTOR_NAME, SPECIALIZATION, AVAILABLE_DAYS)
VALUES ('D05', 'Gdoc', 'General Medicine', 'Monday, Wednesday');
INSERT INTO DOCTOR_SCHEDULE (DOCTOR_ID, DOCTOR_NAME, SPECIALIZATION, AVAILABLE_DAYS)
VALUES ('D12', 'Gdoc1', 'General Medicine', 'Tuesday, Thursday');

COMMIT;
------------------------------


INSERT INTO USERS1 (USER_ID, NAME, ROLE, PASSWORD, SPECIALIZATION)
VALUES ('D20', 'CEmDoc', 'Doctor', 'ce20', 'Cardiology');

INSERT INTO doctor_schedule (DOCTOR_ID, DOCTOR_NAME, SPECIALIZATION, AVAILABLE_DAYS)
VALUES ('D20', 'CEmDoc', 'Cardiology', 'Emergency');

INSERT INTO USERS1 (USER_ID, NAME, ROLE, PASSWORD, SPECIALIZATION)
VALUES ('D21', 'PEmDoc', 'Doctor', 'pe21', 'Pediatrics');

INSERT INTO doctor_schedule (DOCTOR_ID, DOCTOR_NAME, SPECIALIZATION, AVAILABLE_DAYS)
VALUES ('D21', 'PEmDoc', 'Pediatrics', 'Emergency');

INSERT INTO USERS1 (USER_ID, NAME, ROLE, PASSWORD, SPECIALIZATION)
VALUES ('D22', 'OEmDoc', 'Doctor', 'oe22', 'Orthopedics');

INSERT INTO doctor_schedule (DOCTOR_ID, DOCTOR_NAME, SPECIALIZATION, AVAILABLE_DAYS)
VALUES ('D22', 'OEmDoc', 'Orthopedics', 'Emergency');

INSERT INTO USERS1 (USER_ID, NAME, ROLE, PASSWORD, SPECIALIZATION)
VALUES ('D23', 'NEmDoc', 'Doctor', 'ne23', 'Neurology');

INSERT INTO doctor_schedule (DOCTOR_ID, DOCTOR_NAME, SPECIALIZATION, AVAILABLE_DAYS)
VALUES ('D23', 'NEmDoc', 'Neurology', 'Emergency');

INSERT INTO USERS1 (USER_ID, NAME, ROLE, PASSWORD, SPECIALIZATION)
VALUES ('D24', 'GEmDoc', 'Doctor', 'ge24', 'General Medicine');

INSERT INTO doctor_schedule (DOCTOR_ID, DOCTOR_NAME, SPECIALIZATION, AVAILABLE_DAYS)
VALUES ('D24', 'GEmDoc', 'General Medicine', 'Emergency');
-------------------------------------------------------------------------------------------------------------
CREATE TABLE EMERGENCY_QUEUE (
    EMERGENCY_ID NUMBER GENERATED BY DEFAULT ON NULL AS IDENTITY PRIMARY KEY,
    PATIENT_NAME VARCHAR2(100),
    PHONE VARCHAR2(15),
    SPECIALIZATION VARCHAR2(100),
    ASSIGNED_DOCTOR VARCHAR2(20),
    STATUS VARCHAR2(20) DEFAULT 'Waiting',
    REPORTED_AT TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

ALTER TABLE EMERGENCY_QUEUE
ADD CONSTRAINT fk_emergency_doctor FOREIGN KEY (ASSIGNED_DOCTOR) REFERENCES USERS1(USER_ID);

-----------------------------------------------------------------------------------------------------------------
CREATE TABLE walkins (
    TOKEN_NO              NUMBER PRIMARY KEY,
    PATIENT_NAME          VARCHAR2(100),
    AGE                   NUMBER,
    GENDER                VARCHAR2(10),
    CONTACT               VARCHAR2(20),
    SYMPTOMS              CLOB,
    SPECIALIZATION        VARCHAR2(50),
    TRIAGE_LEVEL          VARCHAR2(20),
    ASSIGNED_DOCTOR       VARCHAR2(50),
    APPOINTMENT_DATE      DATE,
    APPOINTMENT_TIME      VARCHAR2(10),
    ESTIMATED_WAITING_TIME VARCHAR2(20),
    STATUS                VARCHAR2(20),
    BOOKING_DATETIME      TIMESTAMP
);

-- General Medicine Walk-in Doctor
INSERT INTO USERS1 (USER_ID, NAME, ROLE, PASSWORD, SPECIALIZATION)
VALUES ('W01', 'WDoc_GM', 'Doctor', 'gmwalkin', 'General Medicine');

INSERT INTO doctor_schedule (DOCTOR_ID, DOCTOR_NAME, SPECIALIZATION, AVAILABLE_DAYS)
VALUES ('W01', 'WDoc_GM', 'General Medicine', 'Walkin');

-- Cardiology Walk-in Doctor
INSERT INTO USERS1 (USER_ID, NAME, ROLE, PASSWORD, SPECIALIZATION)
VALUES ('W02', 'WDoc_Card', 'Doctor', 'cardwalkin', 'Cardiology');

INSERT INTO doctor_schedule (DOCTOR_ID, DOCTOR_NAME, SPECIALIZATION, AVAILABLE_DAYS)
VALUES ('W02', 'WDoc_Card', 'Cardiology', 'Walkin');

-- Neurology Walk-in Doctor
INSERT INTO USERS1 (USER_ID, NAME, ROLE, PASSWORD, SPECIALIZATION)
VALUES ('W03', 'WDoc_Neuro', 'Doctor', 'neurowalkin', 'Neurology');

INSERT INTO doctor_schedule (DOCTOR_ID, DOCTOR_NAME, SPECIALIZATION, AVAILABLE_DAYS)
VALUES ('W03', 'WDoc_Neuro', 'Neurology', 'Walkin');

-- Orthopedics Walk-in Doctor
INSERT INTO USERS1 (USER_ID, NAME, ROLE, PASSWORD, SPECIALIZATION)
VALUES ('W04', 'WDoc_Ortho', 'Doctor', 'orthowalkin', 'Orthopedics');

INSERT INTO doctor_schedule (DOCTOR_ID, DOCTOR_NAME, SPECIALIZATION, AVAILABLE_DAYS)
VALUES ('W04', 'WDoc_Ortho', 'Orthopedics', 'Walkin');

-- Pediatrics Walk-in Doctor
INSERT INTO USERS1 (USER_ID, NAME, ROLE, PASSWORD, SPECIALIZATION)
VALUES ('W05', 'WDoc_Ped', 'Doctor', 'pedwalkin', 'Pediatrics');

INSERT INTO doctor_schedule (DOCTOR_ID, DOCTOR_NAME, SPECIALIZATION, AVAILABLE_DAYS)
VALUES ('W05', 'WDoc_Ped', 'Pediatrics', 'Walkin');



