drop table if exists entry;
create table entry (
    entry_id integer primary key autoincrement,
    title text not null,
    content text not null,
    score integer not null,
    approved integer not null,
    pub_date integer not null
);
drop table if exists mod;
create table mod (
    mod_id integer primary key autoincrement,
    pw_hash text not null
);
