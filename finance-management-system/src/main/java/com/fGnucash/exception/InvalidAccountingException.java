package com.fGnucash.exception;

public class InvalidAccountingException extends RuntimeException{
    public InvalidAccountingException(String message) {
        super(message);
    }
}
