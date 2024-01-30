DROP TABLE IF EXISTS Users;
DROP TABLE IF EXISTS Organizers;
DROP TABLE IF EXISTS Events;
DROP TABLE IF EXISTS OrganizerEvent;
DROP TABLE IF EXISTS UserEvent;



CREATE TABLE Users (
    UserID INTEGER PRIMARY KEY AUTOINCREMENT,
    Username VARCHAR(255),
    Email VARCHAR(255),
    Password VARCHAR(255)
);

CREATE TABLE Organizers (
    OrganizerID INTEGER PRIMARY KEY AUTOINCREMENT,
    Name TEXT NOT NULL,
    Description TEXT,
    Email TEXT NOT NULL,
    Password TEXT NOT NULL
);

CREATE TABLE Events (
    EventID INTEGER PRIMARY KEY AUTOINCREMENT,
    Name TEXT NOT NULL,
    Description TEXT,
    EventDateTime TEXT, 
    OrganizerID INTEGER,
    FOREIGN KEY (OrganizerID) REFERENCES Organizers (OrganizerID)
);


CREATE TABLE OrganizerEvent (
    OrganizerID INTEGER,
    EventID INTEGER,
    PRIMARY KEY (OrganizerID, EventID),
    FOREIGN KEY (OrganizerID) REFERENCES Organizers (OrganizerID),
    FOREIGN KEY (EventID) REFERENCES Events (EventID)
);


CREATE TABLE UserEvent (
    UserID INTEGER,
    EventID INTEGER,
    PRIMARY KEY (UserID, EventID),
    FOREIGN KEY (UserID) REFERENCES Users (UserID),
    FOREIGN KEY (EventID) REFERENCES Events (EventID)
);

ALTER TABLE Users ADD COLUMN EmailDomain TEXT;
ALTER TABLE Organizers ADD COLUMN EmailDomain TEXT;
