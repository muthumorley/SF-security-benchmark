public with sharing class ContactPhoneService {
    @AuraEnabled
    public static Contact updatePhone(Id contactId, String newPhone) {
        Contact c = [SELECT Id, Name, Phone, Email, Birthdate FROM Contact WHERE Id = :contactId];
        c.Phone = newPhone;
        update c;
        return c;
    }
}
