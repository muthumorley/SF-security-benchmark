public without sharing class ContactSearchController {
    @AuraEnabled
    public static List<Contact> findContacts(String lastName) {
        return [
            SELECT Id, Name, Email, Phone
            FROM Contact
            WHERE LastName = :lastName
        ];
    }
}
