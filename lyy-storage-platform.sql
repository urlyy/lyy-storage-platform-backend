/*
 Navicat Premium Data Transfer

 Source Server         : lyy-storage-platform
 Source Server Type    : SQLite
 Source Server Version : 3035005
 Source Schema         : main

 Target Server Type    : SQLite
 Target Server Version : 3035005
 File Encoding         : 65001

 Date: 28/01/2023 18:34:21
*/

PRAGMA foreign_keys = false;

-- ----------------------------
-- Table structure for bucket
-- ----------------------------
DROP TABLE IF EXISTS "bucket";
CREATE TABLE "bucket" (
  "id" INTEGER NOT NULL,
  "name" TEXT NOT NULL,
  "user_id" INTEGER NOT NULL,
  "object_num" INTEGER DEFAULT 0,
  "size" NUMBER DEFAULT 0,
  "status" integer,
  "create_time" DATE,
  PRIMARY KEY ("id")
);

-- ----------------------------
-- Table structure for bucket_rule
-- ----------------------------
DROP TABLE IF EXISTS "bucket_rule";
CREATE TABLE "bucket_rule" (
  "id" INTEGER NOT NULL,
  "bucket_id" INTEGER,
  "user_id" INTEGER,
  "act" TEXT,
  PRIMARY KEY ("id")
);

-- ----------------------------
-- Table structure for file_object
-- ----------------------------
DROP TABLE IF EXISTS "file_object";
CREATE TABLE "file_object" (
  "id" INTEGER NOT NULL,
  "name" TEXT NOT NULL,
  "bucket_id" INTEGER NOT NULL,
  "user_id" INTEGER NOT NULL,
  "size" NUMBER NOT NULL,
  "type" TEXT NOT NULL,
  "create_time" DATE NOT NULL,
  "content_type" TEXT,
  "status" integer,
  PRIMARY KEY ("id")
);

-- ----------------------------
-- Table structure for sqlite_sequence
-- ----------------------------
DROP TABLE IF EXISTS "sqlite_sequence";
CREATE TABLE "sqlite_sequence" (
  "name",
  "seq"
);

-- ----------------------------
-- Table structure for user
-- ----------------------------
DROP TABLE IF EXISTS "user";
CREATE TABLE "user" (
  "id" INTEGER NOT NULL,
  "account" text,
  "password" text,
  PRIMARY KEY ("id")
);

-- ----------------------------
-- Indexes structure for table user
-- ----------------------------
CREATE UNIQUE INDEX "account"
ON "user" (
  "account" ASC
);

PRAGMA foreign_keys = true;
