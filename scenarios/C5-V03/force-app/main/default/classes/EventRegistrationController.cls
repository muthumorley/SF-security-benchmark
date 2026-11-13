public with sharing class EventRegistrationController {
    @AuraEnabled
    public static Id registerForEvent(String email, Id eventId) {
        // VULNERABLE: no email format validation, no rate limiting, no CAPTCHA check.
        // Any anonymous visitor can call this endpoint and insert arbitrary registrations.
        EventRegistration__c reg = new EventRegistration__c(
            Email__c = email,
            Event__c = eventId,
            Registered_At__c = System.now()
        );
        insert reg;
        return reg.Id;
    }
}
