public with sharing class KnowledgeSearchController {
    @AuraEnabled(cacheable=true)
    public static List<KnowledgeArticleVersion> searchArticles(String searchTerm) {
        String term = '%' + String.escapeSingleQuotes(searchTerm) + '%';
        return [SELECT Id, Title, Summary, ArticleNumber
                FROM KnowledgeArticleVersion
                WHERE PublishStatus = 'Online'
                AND Title LIKE :term
                WITH USER_MODE LIMIT 50];
    }
}
