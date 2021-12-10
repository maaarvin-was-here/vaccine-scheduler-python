
CREATE TABLE Caregivers (
    Username varchar(255),
    Salt BINARY(16),
    Hash BINARY(16),
    PRIMARY KEY (Username)
);

CREATE TABLE Patients (
    Username varchar(255),
    Salt BINARY(16),
    Hash BINARY(16),
    PRIMARY KEY (Username)
);

CREATE TABLE Booked (
    id INT IDENTITY(1,1), -- auto-increments ID
    Time date,
    Username varchar(255) REFERENCES Caregivers,
    Patient varchar(255) REFERENCES Patients,
    v_name varchar(255) REFERENCES Vaccines,
    PRIMARY KEY (id)
);

CREATE TABLE Vaccines (
    Name varchar(255),
    Doses int,
    PRIMARY KEY (Name)
);